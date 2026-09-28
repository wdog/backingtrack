"""Interfaccia a riga di comando."""
import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

from . import __version__, packs
from .arranger import Arranger
from .errors import SongError
from .grooves import GROOVES
from .midi import write_midi
from .mixer import mix
from .render import Sampler, make_rng, mix_voices, new_buses
from .sfz import Instrument
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
bass: false           # contrabbasso (serve: backingtrack setup --bass)

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

COMMANDS = ("render", "setup", "remove", "grooves", "new", "doctor")
GUITARS = ("gretsch", "epiphone")


def render_song(path, args):
    t_start = time.time()
    song = load_song(path)
    if args.transpose is not None:
        song["transpose"] = args.transpose
    order, timeline = build_timeline(song, args.groove)
    arr = Arranger(song, args.tempo, args.bass).arrange(timeline)

    out = Path(args.out) if args.out and len(args.songs) == 1 else Path(args.out or "out") / Path(path).stem
    if args.out and len(args.songs) > 1:
        out = Path(args.out) / Path(path).stem
    title = str(song.get("title", out.name))
    secs = arr.seconds(arr.length)
    print("♪ %s | %g BPM | %d battute | %d:%02d" % (title, arr.tempo, len(timeline), secs // 60, secs % 60))
    for sec, reps in order:
        chords = " | ".join(" ".join(c.name if c else "N.C." for _, _, c in segs) for segs in sec["bars"])
        print("   %-12s x%-2d %-19s | %s |" % (sec["name"], reps, "[" + sec["groove"] + "]", chords))
    if args.dry_run:
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    mid = out.with_suffix(".mid")
    write_midi(mid, arr, title)
    if args.midi_only:
        print("   MIDI  %s" % mid)
        return

    mute = {m.strip() for m in (args.mute or "").split(",") if m.strip()}
    unknown = mute - {"guitar", "drums", "bass"}
    if unknown:
        raise SongError("--mute: tracce sconosciute %s (usa guitar, drums, bass)" % ", ".join(sorted(unknown)))

    rng = make_rng(song.get("seed", 1))
    groups = {"guitar": [], "drums": [], "bass": []}
    for n in arr.notes:
        fam = "guitar" if n.part.startswith("guitar") else n.part
        if fam in mute:
            continue
        groups[fam].append(dict(start=arr.seconds(n.start), end=arr.seconds(n.end), key=n.pitch,
                                vel=n.vel, muted=n.muted, bus=n.bus))
    bus_names = {v["bus"] for g in groups.values() for v in g}
    if not bus_names:
        raise SongError("tutte le tracce sono mutate")
    buses = new_buses(bus_names, secs + 4)

    if groups["guitar"]:
        pack = str(song.get("guitar", "gretsch"))
        if pack not in GUITARS:
            raise SongError("guitar: '%s' sconosciuta (usa %s)" % (pack, ", ".join(GUITARS)))
        notes = groups["guitar"]
        mute_sfz = packs.sfz_path(pack, "mute_sfz")
        if mute_sfz:  # note stoppate con i veri campioni staccato
            muted = [dict(n, muted="real") for n in notes if n["muted"]]
            notes = [n for n in notes if not n["muted"]]
            mix_voices(Sampler(_instrument(pack, "mute_sfz")).voices(muted, rng), buses)
        mix_voices(Sampler(_instrument(pack)).voices(notes, rng), buses)
    if groups["drums"]:
        drum_map = packs.PACKS["drums"]["drum_map"]

        def cc_for(key):
            k, cc4 = drum_map.get(key, (key, None))
            return k, ({4: cc4} if cc4 is not None else None)

        s = Sampler(_instrument("drums"), vel_exp=0.55)
        mix_voices(s.voices(groups["drums"], rng, cc_for), buses)
    if groups["bass"]:
        s = Sampler(_instrument("bass"))
        mix_voices(s.voices(groups["bass"], rng), buses)

    wav = out.with_suffix(".wav")
    mp3 = out.with_suffix(".mp3") if args.mp3 else None
    stems = out.parent / (out.name + "_stems") if args.stems else None
    with tempfile.TemporaryDirectory(prefix="backingtrack-") as tmp:
        cabs = packs.pack_dir("cabs") if packs.is_installed("cabs") else None
        mix(buses, wav, tmp, mp3=mp3, stems_dir=stems, cab_dir=cabs)
    print("   WAV   %s" % wav)
    for label, p in (("MP3", mp3), ("STEMS", stems)):
        if p:
            print("   %-5s %s" % (label, p))
    print("   MIDI  %s   (%.1fs)" % (mid, time.time() - t_start))


_INSTRUMENTS = {}


def _instrument(name, key="sfz"):
    if (name, key) not in _INSTRUMENTS:
        _INSTRUMENTS[name, key] = Instrument(packs.sfz_path(name, key))
    return _INSTRUMENTS[name, key]


def cmd_setup(args):
    names = list(args.packs) or list(packs.DEFAULT_PACKS)
    if args.bass and "bass" not in names:
        names.append("bass")
    unknown = [n for n in names if n not in packs.PACKS]
    if unknown:
        raise SongError("pacchetti sconosciuti: %s (disponibili: %s)" % (", ".join(unknown), ", ".join(packs.PACKS)))
    for n in names:
        packs.install(n, force=args.force or args.full, full=args.full)
    print("\nPronto. Prova:  backingtrack examples/blues/sweet_home_chicago.yaml")


def cmd_remove(args):
    for n in args.packs:
        if n not in packs.PACKS:
            raise SongError("pacchetto sconosciuto: %s" % n)
        packs.remove(n)


def cmd_doctor(_args):
    ok = True
    print("backingtrack %s — Python %s" % (__version__, sys.version.split()[0]))
    for tool in ("ffmpeg",):
        path = shutil.which(tool)
        ok &= bool(path)
        print("  %s %-8s %s" % ("✓" if path else "✗", tool, path or "NON trovato"))
    for mod in ("numpy", "yaml"):
        try:
            __import__(mod)
            print("  ✓ %-8s ok" % mod)
        except ImportError:
            ok = False
            print("  ✗ %-8s mancante (pip install numpy pyyaml)" % mod)
    print("  campioni in %s" % (packs.data_dir() / "packs"))
    for name, state, title, lic in packs.status():
        print("  %s %-8s %-10s %s [%s]" % ("✓" if state.startswith("installato") else "·", name, state, title, lic))
    if not ok:
        sys.exit(1)


def build_parser():
    ap = argparse.ArgumentParser(
        prog="backingtrack",
        description="Backing track realistiche (chitarra + batteria) da un file YAML di accordi.")
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = ap.add_subparsers(dest="command")

    r = sub.add_parser("render", help="genera WAV/MIDI da uno o più file canzone")
    r.add_argument("songs", nargs="+", help="file YAML")
    r.add_argument("-o", "--out", help="output senza estensione (più file: cartella). Default out/<nome>")
    r.add_argument("-t", "--tempo", type=float, help="sovrascrive il tempo (BPM)")
    r.add_argument("-g", "--groove", help="forza un groove per tutte le sezioni")
    r.add_argument("--transpose", type=int, help="sovrascrive la trasposizione (semitoni)")
    r.add_argument("--bass", action="store_true", help="aggiunge il contrabbasso")
    r.add_argument("--mute", help="tracce da escludere: guitar, drums, bass (separate da virgola)")
    r.add_argument("--mp3", action="store_true", help="crea anche un mp3")
    r.add_argument("--stems", action="store_true", help="salva le tracce separate")
    r.add_argument("--midi-only", action="store_true", help="solo MIDI")
    r.add_argument("--dry-run", action="store_true", help="mostra la struttura senza scrivere file")

    s = sub.add_parser("setup", help="scarica e installa i campioni")
    s.add_argument("packs", nargs="*", help="pacchetti (default: %s)" % " ".join(packs.DEFAULT_PACKS))
    s.add_argument("--bass", action="store_true", help="aggiunge il contrabbasso (~45 MB)")
    s.add_argument("--full", action="store_true", help="tutti i round robin: qualità massima, ~4 volte più grande")
    s.add_argument("--force", action="store_true", help="reinstalla")
    rm = sub.add_parser("remove", help="cancella pacchetti di campioni")
    rm.add_argument("packs", nargs="+")

    sub.add_parser("grooves", help="elenca i groove")
    n = sub.add_parser("new", help="crea un file canzone di esempio")
    n.add_argument("file")
    sub.add_parser("doctor", help="controlla dipendenze e campioni")
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
        elif args.command == "grooves":
            for k, g in GROOVES.items():
                print("  %-19s %s" % (k, g["desc"]))
        elif args.command == "new":
            p = Path(args.file)
            if p.exists():
                raise SongError("%s esiste già" % p)
            p.write_text(TEMPLATE, encoding="utf-8")
            print("creato %s — modificalo e poi: backingtrack %s" % (p, p))
        elif args.command == "doctor":
            cmd_doctor(args)
        else:
            ap.print_help()
    except SongError as e:
        sys.exit("errore: %s" % e)
    except KeyboardInterrupt:
        sys.exit(130)
