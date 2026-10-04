"""Interfaccia a riga di comando."""
import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import __version__, packs, term
from .arranger import Arranger
from .errors import SongError
from .grooves import GROOVES
from .i18n import _, groove_desc, lang
from .midi import write_midi
from .mixer import mix
from .render import Sampler, make_rng, mix_voices, new_buses
from .sfz import Instrument, read_wav
from .song import build_timeline, load_song

TEMPLATE = """\
# Canzone per backingtrack — vedi README.md
title: La mia canzone
tempo: 110            # BPM
groove: blues         # backingtrack grooves
transpose: 0          # semitoni (+2 = un tono sopra)
count_in: true        # una battuta di bacchette prima di partire
ending: true          # accordo finale con piatto
fills: true           # rullata sull'ultima battuta di ogni sezione
bass: false           # true = contrabbasso, oppure ebass / sneakybass (serve: backingtrack setup <nome>)

sections:
  - name: Intro
    chords: "| E7 | D7 | A7 | E7 |"

  - name: Strofa
    repeat: 2           # suona 2 volte questa sezione
    chords: |
      | A7 | D7 | A7 | %  |
      | D7 | %  | A7 | %  |
      | E7 | D7 | A7 | E7 |

# ordine opzionale; senza arrangement le sezioni suonano in fila
# arrangement: [Intro, Strofa x2, Intro]
"""

TEMPLATE_EN = """\
# Song for backingtrack — see README.md
title: My song
tempo: 110            # BPM
groove: blues         # backingtrack grooves
transpose: 0          # semitones (+2 = one tone up)
count_in: true        # one bar of sticks before starting
ending: true          # final chord with cymbal
fills: true           # drum fill on the last bar of every section
bass: false           # true = double bass, or ebass / sneakybass (needs: backingtrack setup <name>)

sections:
  - name: Intro
    chords: "| E7 | D7 | A7 | E7 |"

  - name: Verse
    repeat: 2           # play this section twice
    chords: |
      | A7 | D7 | A7 | %  |
      | D7 | %  | A7 | %  |
      | E7 | D7 | A7 | E7 |

# optional order; without arrangement the sections play one after the other
# arrangement: [Intro, Verse x2, Intro]
"""

COMMANDS = ("render", "setup", "remove", "update", "grooves", "new", "doctor", "gui")
GUITARS = tuple(packs.GUITAR_PACKS)


def render_song(path, args):
    song = load_song(path)
    if args.transpose is not None:
        song["transpose"] = args.transpose
    out = Path(args.out) if args.out and len(args.songs) == 1 else Path(args.out or "out") / Path(path).stem
    if args.out and len(args.songs) > 1:
        out = Path(args.out) / Path(path).stem
    render(song, out, tempo=args.tempo, groove=args.groove, bass=args.bass, mute=args.mute, mp3=args.mp3,
           stems=args.stems, midi_only=args.midi_only, dry_run=args.dry_run)


def render(song, out, tempo=None, groove=None, bass=False, mute=None, mp3=False, stems=False,
           midi_only=False, dry_run=False, log=print):
    """Genera i file per un brano (dict già caricato). Ritorna {"wav", "mp3", "mid", "stems"}."""
    t_start = time.time()
    out = Path(out)
    order, timeline = build_timeline(song, groove)
    arr = Arranger(song, tempo, bass).arrange(timeline)
    title = str(song.get("title", out.name))
    secs = arr.seconds(arr.length)
    log(_("♪ %s | %g BPM | %d battute | %d:%02d") % (title, arr.tempo, len(timeline), secs // 60, secs % 60))
    for sec, reps in order:
        chords = " | ".join(" ".join(c.name if c else "N.C." for _, _, c in segs) for segs in sec["bars"])
        log("   %-12s x%-2d %-19s | %s |" % (sec["name"], reps, "[" + sec["groove"] + "]", chords))
    result = {}
    if dry_run:
        return result

    out.parent.mkdir(parents=True, exist_ok=True)
    result["mid"] = mid = out.with_suffix(".mid")
    write_midi(mid, arr, title)
    if midi_only:
        log("   MIDI  %s" % mid)
        return result

    if isinstance(mute, str):
        mute = mute.split(",")
    mute = {m.strip() for m in (mute or ()) if m.strip()}
    unknown = mute - {"guitar", "drums", "bass"}
    if unknown:
        raise SongError(_("--mute: tracce sconosciute %s (usa guitar, drums, bass)") % ", ".join(sorted(unknown)))

    rng = make_rng(song.get("seed", 1))
    groups = {"guitar": [], "drums": [], "bass": []}
    for n in arr.notes:
        fam = "guitar" if n.part.startswith("guitar") else n.part
        if fam in mute:
            continue
        groups[fam].append(dict(start=arr.seconds(n.start), end=arr.seconds(n.end), key=n.pitch,
                                vel=n.vel, muted=n.muted, bus=n.bus))
    pack = str(song.get("guitar", "fender"))
    if groups["guitar"]:
        if pack not in GUITARS:
            raise SongError(_("guitar: '%s' sconosciuta (usa %s)") % (pack, ", ".join(GUITARS)))
        amp = packs.PACKS[pack].get("amp")
        if amp:  # chitarra con catena propria (acustica): sostituisce l'ampli del groove
            for n in groups["guitar"]:
                n["bus"] = "gtr:%s:%s" % (amp, n["bus"].split(":", 2)[2])
    bus_names = {v["bus"] for g in groups.values() for v in g}
    if not bus_names:
        raise SongError(_("tutte le tracce sono mutate"))
    buses = new_buses(bus_names, secs + 4)

    if groups["guitar"]:
        notes = groups["guitar"]
        mute_sfz = packs.sfz_path(pack, "mute_sfz")
        if mute_sfz:  # note stoppate con i veri campioni staccato
            muted = [dict(n, muted="real") for n in notes if n["muted"]]
            notes = [n for n in notes if not n["muted"]]
            mix_voices(Sampler(_instrument(pack, "mute_sfz"), detune=4).voices(muted, rng), buses)
        mix_voices(Sampler(_instrument(pack), detune=4).voices(notes, rng), buses)
    if groups["drums"]:
        drum_map = packs.PACKS["drums"]["drum_map"]

        def cc_for(key):
            k, cc4 = drum_map.get(key, (key, None))
            return k, ({4: cc4} if cc4 is not None else None)

        s = Sampler(_instrument("drums"), vel_exp=0.55)
        mix_voices(s.voices(groups["drums"], rng, cc_for), buses)
    if groups["bass"]:
        s = Sampler(_instrument(packs.bass_pack(song.get("bass")) or "bass"))
        mix_voices(s.voices(groups["bass"], rng), buses)

    for ins in _INSTRUMENTS.values():
        ins.save_tuning()

    wav = out.with_suffix(".wav")
    mp3 = out.with_suffix(".mp3") if mp3 else None
    stems = out.parent / (out.name + "_stems") if stems else None
    with tempfile.TemporaryDirectory(prefix="backingtrack-") as tmp:
        cabs = packs.pack_dir("cabs") if packs.is_installed("cabs") else None
        mix(buses, wav, tmp, mp3=mp3, stems_dir=stems, cab_dir=cabs)
    log("   WAV   %s" % wav)
    for label, p in (("MP3", mp3), ("STEMS", stems)):
        if p:
            log("   %-5s %s" % (label, p))
    log("   MIDI  %s   (%.1fs)" % (mid, time.time() - t_start))
    result.update(wav=wav, mp3=mp3, stems=stems)
    return result


_INSTRUMENTS = {}


def _instrument(name, key="sfz"):
    if (name, key) not in _INSTRUMENTS:
        # chitarre e basso: i campioni hanno scarti d'intonazione fissi fino a ~30 cent, che negli accordi battono
        _INSTRUMENTS[name, key] = Instrument(packs.sfz_path(name, key), autotune=name != "drums",
                                             root=packs.pack_dir(name), cc=packs.PACKS[name].get("cc"))
    return _INSTRUMENTS[name, key]


def cmd_setup(args):
    names = list(args.packs) or list(packs.DEFAULT_PACKS)
    if args.bass and "bass" not in names:
        names.append("bass")
    unknown = [n for n in names if n not in packs.PACKS]
    if unknown:
        raise SongError(_("pacchetti sconosciuti: %s (disponibili: %s)") % (", ".join(unknown), ", ".join(packs.PACKS)))
    term.banner(_("campioni"))
    term.section(_("Campioni"), str(packs.data_dir() / "packs"))
    for n in names:
        packs.install(n, force=args.force or args.full, full=args.full)
    term.done(_("Pronto!"), _("prova:  backingtrack examples/blues/sweet_home_chicago.yaml"))


def cmd_remove(args):
    for n in args.packs:
        if n not in packs.PACKS:
            raise SongError(_("pacchetto sconosciuto: %s") % n)
    print()
    for n in args.packs:
        packs.remove(n)


REPO_URL = "https://github.com/wdog/backingtrack.git"


def cmd_update(args):
    """Scarica i campioni mancanti (quelli presenti restano) e aggiorna il programma."""
    names = list(packs.DEFAULT_PACKS) + [n for n in packs.PACKS if n not in packs.DEFAULT_PACKS and packs.is_installed(n)]
    term.banner(_("aggiornamento"))
    term.section(_("Campioni"), str(packs.data_dir() / "packs"))
    for n in names:
        packs.install(n)  # salta i pacchetti già installati

    term.section(_("Programma"))
    src = Path(__file__).resolve().parent.parent
    if (src / ".git").exists() and not (args.force or args.src):
        term.row(term.DOT, _("sviluppo"), str(src))
        term.done(_("Campioni aggiornati"), _("il codice si aggiorna con  git pull"))
        return
    if args.src:
        spec = str(Path(args.src).resolve())
    elif shutil.which("git"):
        spec = "git+%s@%s" % (REPO_URL, args.ref)
    else:
        spec = "https://github.com/wdog/backingtrack/archive/%s.zip" % args.ref
    term.row(term.DOWN, _("sorgente"), spec)
    if "pipx" in sys.prefix and shutil.which("pipx"):
        # reinstallazione completa: mantiene --system-site-packages (serve alla GUI per vedere GTK)
        subprocess.run(["pipx", "uninstall", "backingtrack"], stdout=subprocess.DEVNULL)
        cmd = ["pipx", "install", "--system-site-packages", spec]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", spec]
    term.note(" ".join(cmd[:3]) + " …")
    if subprocess.run(cmd, stdout=subprocess.DEVNULL).returncode != 0:
        raise SongError(_("aggiornamento non riuscito. Riprova o usa l'installer:  "
                        "curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash"))
    term.done(_("Aggiornato!"), _("novità nel README: https://github.com/wdog/backingtrack#readme"))


def _install_hint(what):
    """Comando per installare una dipendenza di sistema sulla piattaforma corrente."""
    import platform
    system = platform.system()
    hints = {
        "ffmpeg": {"Darwin": "brew install ffmpeg", "Windows": "winget install Gyan.FFmpeg"},
        "gui": {"Darwin": "brew install pygobject3 gtk4 libadwaita",
                "Windows": _("la GUI su Windows richiede MSYS2 (vedi README)")},
    }
    if system in hints[what]:
        return hints[what][system]
    for mgr, cmd in (("apt-get", {"ffmpeg": "sudo apt install ffmpeg",
                                  "gui": "sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1"}),
                     ("dnf", {"ffmpeg": "sudo dnf install ffmpeg", "gui": "sudo dnf install python3-gobject gtk4 libadwaita"}),
                     ("pacman", {"ffmpeg": "sudo pacman -S ffmpeg", "gui": "sudo pacman -S python-gobject gtk4 libadwaita"})):
        if shutil.which(mgr):
            return cmd[what]
    return _("installa %s con il gestore pacchetti del sistema") % what


def _install_kind():
    src = Path(__file__).resolve().parent.parent
    if (src / ".git").exists():
        return _("sviluppo (%s)") % src
    if "pipx" in sys.prefix:
        return "pipx (%s)" % sys.prefix
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return "virtualenv (%s)" % sys.prefix
    return _("Python di sistema")


def _dir_mb(path):
    path = Path(path)
    if not path.exists():
        return 0.0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 2 ** 20


def cmd_doctor(_args):
    import random
    line, todo = term.row, []
    ok_s, bad_s, warn_s = term.OK, term.BAD, term.WARN

    term.banner(_("diagnosi"))
    term.section(_("Programma"))
    line(ok_s, _("versione"), __version__)
    line(ok_s, _("installato"), _install_kind())
    line(ok_s, "python", sys.version.split()[0], sys.executable)
    cmd = shutil.which("backingtrack")
    line(ok_s if cmd else warn_s, _("comando"), cmd or _("(non nel PATH: usa python -m backingtrack)"))

    term.section(_("Dipendenze"))
    ff = shutil.which("ffmpeg")
    if ff:
        ver = subprocess.run([ff, "-version"], stdout=subprocess.PIPE, universal_newlines=True).stdout.split("\n")[0]
        line(ok_s, "ffmpeg", ver.split(" Copyright")[0].replace("ffmpeg version ", ""), ff)
    else:
        line(bad_s, "ffmpeg", _("NON trovato"), _("serve per mix e mp3"))
        todo.append((_("installa ffmpeg"), _install_hint("ffmpeg")))
    for mod, label in (("numpy", "numpy"), ("yaml", "PyYAML")):
        try:
            m = __import__(mod)
            line(ok_s, label, getattr(m, "__version__", "ok"))
        except ImportError:
            line(bad_s, label, _("mancante"))
            todo.append((_("installa %s") % label, "pip install numpy pyyaml"))
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw, Gtk
        line(ok_s, "GUI", "GTK %d.%d · libadwaita %d.%d" % (Gtk.get_major_version(), Gtk.get_minor_version(),
                                                           Adw.get_major_version(), Adw.get_minor_version()),
             "backingtrack gui")
    except (ImportError, ValueError) as e:
        line(warn_s, "GUI", _("non disponibile (opzionale)"), str(e).split("\n")[0][:60])
        hint = _install_hint("gui")
        if "pipx" in sys.prefix:
            hint += _("  poi  pipx reinstall --system-site-packages backingtrack")
        todo.append((_("per la GUI installa GTK 4 e libadwaita"), hint))

    sizes = {n: packs.disk_mb(n) for n in packs.PACKS if packs.is_installed(n)}
    term.section(_("Campioni"), _("%.0f MB in totale") % sum(sizes.values()))
    term.note(str(packs.data_dir() / "packs"))
    biggest = max(sizes.values(), default=1) or 1
    for name, info in packs.PACKS.items():
        title = _(info["title"]).split(" — ")[0]
        if name in sizes:
            # integrità: rileggo qualche campione a caso (scopre file corrotti o troncati)
            files = [f for f in packs.pack_dir(name).rglob("*.wav")]
            bad = 0
            for f in random.sample(files, min(12, len(files))):
                try:
                    read_wav(f)
                except (ValueError, OSError):
                    bad += 1
            if bad:
                line(bad_s, name, _("%d file illeggibili su %d controllati") % (bad, min(12, len(files))))
                todo.append((_("reinstalla i campioni '%s'") % name, "backingtrack setup %s --force" % name))
            else:
                line(ok_s, name, "%s %4.0f MB  %s" % (term.bar(sizes[name] / biggest, 8), sizes[name], title),
                     _("%d file") % len(files))
        elif info.get("default"):
            line(bad_s, name, _("mancante  %s") % title, "~%d MB" % info.get("light_mb", 0))
            todo.append((_("scarica i campioni"), "backingtrack setup"))
        else:
            line(term.OFF, name, _("non installato  %s") % title, _("opzionale: backingtrack setup %s") % name)

    term.section(_("Cartelle"))
    line(ok_s, _("dati"), packs.data_dir())
    cache = packs.cache_dir()
    line(ok_s, "cache", cache, "%.0f MB" % _dir_mb(cache))
    line(ok_s, "output", Path("out").resolve(), _("default di render"))

    todo = list(dict.fromkeys(todo))
    if todo:
        term.todo(_("Da sistemare:"), todo)
        if any(what != _("per la GUI installa GTK 4 e libadwaita") for what, _cmd in todo):
            sys.exit(1)
    else:
        term.done(_("Tutto pronto! 🎸"), _("prova:  backingtrack examples/blues/sweet_home_chicago.yaml"))


def build_parser():
    ap = argparse.ArgumentParser(
        prog="backingtrack",
        description=_("Backing track realistiche (chitarra + batteria) da un file YAML di accordi."))
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = ap.add_subparsers(dest="command")

    r = sub.add_parser("render", help=_("genera WAV/MIDI da uno o più file canzone"))
    r.add_argument("songs", nargs="+", help=_("file YAML"))
    r.add_argument("-o", "--out", help=_("output senza estensione (più file: cartella). Default out/<nome>"))
    r.add_argument("-t", "--tempo", type=float, help=_("sovrascrive il tempo (BPM)"))
    r.add_argument("-g", "--groove", help=_("forza un groove per tutte le sezioni"))
    r.add_argument("--transpose", type=int, help=_("sovrascrive la trasposizione (semitoni)"))
    r.add_argument("--bass", action="store_true", help=_("aggiunge il contrabbasso"))
    r.add_argument("--mute", help=_("tracce da escludere: guitar, drums, bass (separate da virgola)"))
    r.add_argument("--mp3", action="store_true", help=_("crea anche un mp3"))
    r.add_argument("--stems", action="store_true", help=_("salva le tracce separate"))
    r.add_argument("--midi-only", action="store_true", help=_("solo MIDI"))
    r.add_argument("--dry-run", action="store_true", help=_("mostra la struttura senza scrivere file"))

    s = sub.add_parser("setup", help=_("scarica e installa i campioni"))
    s.add_argument("packs", nargs="*", help=_("pacchetti (default: %s)") % " ".join(packs.DEFAULT_PACKS))
    s.add_argument("--bass", action="store_true", help=_("aggiunge il contrabbasso (~45 MB)"))
    s.add_argument("--full", action="store_true", help=_("tutti i round robin: qualità massima, ~4 volte più grande"))
    s.add_argument("--force", action="store_true", help=_("reinstalla"))
    rm = sub.add_parser("remove", help=_("cancella pacchetti di campioni"))
    rm.add_argument("packs", nargs="+")
    up = sub.add_parser("update", help=_("aggiorna il programma e scarica solo i campioni mancanti"))
    up.add_argument("--ref", default="main", help=_("branch o tag da installare (default main)"))
    up.add_argument("--src", help=_("aggiorna da una cartella locale (per provare prima di pubblicare)"))
    up.add_argument("--force", action="store_true", help=_("aggiorna anche un'installazione di sviluppo"))

    sub.add_parser("grooves", help=_("elenca i groove"))
    n = sub.add_parser("new", help=_("crea un file canzone di esempio"))
    n.add_argument("file")
    sub.add_parser("doctor", help=_("controlla dipendenze e campioni"))
    gp = sub.add_parser("gui", help=_("apre l'editor grafico (GTK)"))
    gp.add_argument("file", nargs="?", help=_("brano da aprire"))
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "render")  # scorciatoia: backingtrack song.yaml
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        if args.command == "render":
            for i, song in enumerate(args.songs):
                if i:
                    print()
                render_song(song, args)
        elif args.command == "setup":
            cmd_setup(args)
        elif args.command == "remove":
            cmd_remove(args)
        elif args.command == "update":
            cmd_update(args)
        elif args.command == "grooves":
            for k, g in GROOVES.items():
                print("  %-19s %s" % (k, groove_desc(k, g["desc"])))
        elif args.command == "new":
            p = Path(args.file)
            if p.exists():
                raise SongError(_("%s esiste già") % p)
            p.write_text(TEMPLATE if lang() == "it" else TEMPLATE_EN, encoding="utf-8")
            print(_("creato %s — modificalo e poi: backingtrack %s") % (p, p))
        elif args.command == "doctor":
            cmd_doctor(args)
        elif args.command == "gui":
            from .gui import main as gui_main
            sys.exit(gui_main([args.file] if args.file else []))
        else:
            ap.print_help()
    except SongError as e:
        sys.exit(_("errore: %s") % e)
    except KeyboardInterrupt:
        sys.exit(130)
