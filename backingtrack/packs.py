"""Pacchetti di campioni (SFZ): download, estrazione e conversione, una volta sola."""
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import threading
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import term
from .i18n import _
from .errors import SongError

# GM -> (tasto Salamander, CC4 hi-hat)
SALAMANDER_MAP = {
    35: (35, None), 36: (36, None), 37: (41, None), 38: (38, None), 40: (40, None),
    42: (42, 127), 44: (44, None), 46: (46, None),
    41: (43, None), 43: (43, None), 45: (43, None), 47: (45, None), 48: (45, None), 50: (45, None),
    49: (55, None), 57: (57, None), 51: (48, None), 53: (49, None), 52: (59, None),
}

PACKS = {
    "gretsch": dict(
        title="Black & Green Guitars — Gretsch Anniversary hollowbody, ogni semitono, 4 round robin, staccato",
        author="Karoryfer Samples", license="CC0-1.0",
        repo="sfzinstruments/karoryfer.black-and-green-guitars", sfz="Programs/04-green_twang.sfz",
        mute_sfz="Programs/05-green_staccato.sfz", size_mb=270, light_mb=175, rr=2, keys=range(36, 90),
        exclude=("Samples/black/", "GUI/"), default=True, kind="guitar"),
    "drums": dict(
        title="Salamander Drumkit — batteria acustica, fino a 20 round robin",
        author="Alexander Holm", license="CC-BY-SA-3.0",
        repo="studiorack/salamander-drumkit", sfz="Salamander Drumkit.sfz", size_mb=185, light_mb=120, rr=6,
        keys=sorted({k for k, _ in SALAMANDER_MAP.values()}),
        drum_map=SALAMANDER_MAP, default=True),
    "cabs": dict(
        title="Jester's Emerald + Brutal IR — casse Marshall 4x12 (Greenback, V30) per la simulazione ampli",
        author="Jester Dyne Productions", license="gratuite, anche per uso commerciale",
        urls=[("cabs_emerald.zip",
               "https://www.jester-dyne-productions.com/content/files/2023/04/Emerald-Pack-1.0.zip"),
              ("cabs_brutal.zip",
               "https://www.jester-dyne-productions.com/content/files/2023/04/JestersBrutalPack_1.0.zip")],
        include=("44.1kHz/",), flatten=True, size_mb=5, light_mb=5, default=True),
    "bass": dict(
        title="Contrabbasso Rubner 1958 pizzicato (per --bass)",
        author="D. Smolken", license="CC0-1.0",
        repo="sfzinstruments/dsmolken.double-bass", sfz="d_smolken_rubner_bass_pizz.sfz", size_mb=130,
        light_mb=56, rr=2, keys=range(24, 64),
        exclude=("arco/",), kind="bass"),
    "epiphone": dict(
        title="Emilyguitar — Epiphone solid body (alternativa: guitar: epiphone)",
        author="Karoryfer Samples / D. Smolken", license="CC0-1.0",
        repo="sfzinstruments/karoryfer.emilyguitar", sfz="emily_clean.sfz", size_mb=100, light_mb=40, rr=1,
        keys=range(36, 90), kind="guitar"),
    "acoustic": dict(
        title="FSS Steel-String — chitarra acustica Seagull, quasi ogni semitono, 2 dinamiche (guitar: acoustic)",
        author="FreePats / FlameStudios", license="GPL-3.0+ con eccezione per i brani",
        urls=[("acoustic.tar.xz",
               "https://freepats.zenvoid.org/Guitar/FSS-SteelStringGuitar/FSS-SteelStringGuitar-SFZ-20200521.tar.xz")],
        sfz="FSS-SteelStringGuitar-20200521.sfz", size_mb=25, light_mb=25, amp="acoustic", kind="guitar"),
    "fender": dict(
        title="Electric Guitar FSBS — Fender solid body DI, pickup al ponte, 4 round robin (guitar: fender)",
        author="FreePats", license="CC0-1.0",
        repo="freepats/electric-guitar-FSBS-direct", sfz="EGuitarFSBS-direct bridge 20220911.sfz",
        size_mb=314, light_mb=160, rr=2, keys=range(36, 90), default=True, kind="guitar"),
    "ebass": dict(
        title="Black & Blue Basses 'darkblack' — basso elettrico a dita (bass: ebass)",
        author="Karoryfer Samples", license="CC0-1.0",
        repo="sfzinstruments/karoryfer.black-and-blue-basses", sfz="Programs/05-darkblack_pluck.sfz",
        size_mb=160, light_mb=80, rr=2, keys=range(24, 64), exclude=("GUI/",), kind="bass"),
    "sneakybass": dict(
        title="Sneakybass — contrabbasso Rubner 1958 pizzicato leggero, da jazz notturno (bass: sneakybass)",
        author="D. Smolken", license="CC0-1.0",
        repo="sfzinstruments/karoryfer.sneakybass", sfz="Programs/02-sneakybass_pluck.sfz",
        size_mb=124, light_mb=63, rr=2, keys=range(24, 64), exclude=("GUI/",), kind="bass"),
}
GUITAR_PACKS = [n for n, p in PACKS.items() if p.get("kind") == "guitar"]
BASS_PACKS = [n for n, p in PACKS.items() if p.get("kind") == "bass"]


def bass_pack(value):
    """Valore di `bass:` nel YAML -> pacchetto (None = niente basso). true = contrabbasso 'bass'."""
    if value in (None, False, "", "false", "no"):
        return None
    if value is True or value in ("true", "sì", "si", "yes"):
        return "bass"
    if value in BASS_PACKS:
        return value
    raise SongError(_("bass: '%s' sconosciuto (usa true/false o %s)") % (value, ", ".join(BASS_PACKS)))
DEFAULT_PACKS = [n for n, p in PACKS.items() if p.get("default")]


def _base_dir(kind):
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")) / "backingtrack"
        return base / ("cache" if kind == "cache" else "data")
    if system == "Darwin":
        return home / "Library" / ("Caches" if kind == "cache" else "Application Support") / "backingtrack"
    env = "XDG_CACHE_HOME" if kind == "cache" else "XDG_DATA_HOME"
    default = home / (".cache" if kind == "cache" else ".local/share")
    return Path(os.environ.get(env, default)) / "backingtrack"


def data_dir():
    return Path(os.environ["BACKINGTRACK_HOME"]) if os.environ.get("BACKINGTRACK_HOME") else _base_dir("data")


def cache_dir():
    return _base_dir("cache")


def pack_dir(name):
    return data_dir() / "packs" / name


def is_installed(name):
    return (pack_dir(name) / ".installed").is_file()


def sfz_path(name, key="sfz"):
    if not is_installed(name):
        hint = "" if PACKS[name].get("default") else " " + name
        raise SongError(_("campioni '%s' non installati. Esegui:  backingtrack setup%s") % (name, hint))
    rel = PACKS[name].get(key)
    return pack_dir(name) / rel if rel else None


def print_progress(done, total, files=None):
    """Avanzamento del download sul terminale (sovrascrive la riga): barra sfumata, MB e file."""
    if total:
        line = "      %s %s  %s" % (term.bar(done / total), term.paint(term.PINK, "%3d%%" % (100 * done // total), True),
                                   "%.1f / %.1f MB" % (done / 2 ** 20, total / 2 ** 20))
    else:
        line = "      %.1f MB" % (done / 2 ** 20)
    if files:
        line += term.dim(_("  (%d/%d file)") % files)
    sys.stdout.write("\r" + line + ("\033[K" if term.enabled() else ""))
    sys.stdout.flush()


def _download(url, dest, progress):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "backingtrack"})
    with urllib.request.urlopen(req) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = r.read(1 << 17)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            progress(done, total)
    if progress is print_progress:
        print()
    tmp.replace(dest)


def _flac_to_wav(ffmpeg, flac):
    wav = flac.with_suffix(".wav")
    subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(flac), "-c:a", "pcm_s16le", str(wav)],
                   check=True, stdin=subprocess.DEVNULL)
    flac.unlink()


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "backingtrack"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _needed_samples(info, dest, tree_paths):
    """Legge gli SFZ e ritorna i percorsi (nel repo) dei campioni che il programma usa davvero."""
    from .sfz import Region, parse  # import locale: sfz dipende da numpy
    by_name = {}
    for path in tree_paths:
        by_name.setdefault(path.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower(), path)
    keys = set(info.get("keys") or range(128))
    rr = info.get("rr")
    needed = set()
    for key in ("sfz", "mute_sfz"):
        if not info.get(key):
            continue
        sfz_file = dest / info[key]
        control, ops_list = parse(sfz_file)
        default_path = control.get("default_path", "").replace("\\", "/")
        cc_def = {int(k[6:]): int(float(v)) for k, v in control.items() if k.startswith("set_cc")}
        cc_def.update(info.get("cc") or {})
        groups = {}
        for i, ops in enumerate(ops_list):
            if "sample" not in ops:
                continue
            r = Region(ops, sfz_file.parent, default_path, i)
            if r.trigger not in ("attack", "first") or not keys & set(range(r.lokey, r.hikey + 1)):
                continue
            if any(not (lo <= cc_def.get(n, 0) <= hi) for n, (lo, hi) in r.cc.items()):
                continue
            gkey = (r.lokey, r.hikey, r.lovel, r.hivel, tuple(sorted(r.cc.items())))
            groups.setdefault(gkey, []).append(r)
        for regions in groups.values():
            regions.sort(key=lambda r: (r.lorand, r.seq_position))
            samples = []
            for r in regions:
                if r.sample not in samples:
                    samples.append(r.sample)
            for sample in samples[:rr] if rr else samples:
                try:
                    rel = sample.resolve().relative_to(dest.resolve()).as_posix()
                except ValueError:
                    rel = None
                if rel not in tree_paths:
                    rel = by_name.get(sample.stem.lower())
                if rel:
                    needed.add(rel)
    return needed


def _install_selective(name, info, dest, full, progress):
    """Scarica solo definizioni SFZ e campioni necessari, file per file."""
    import json
    tree = json.loads(_fetch("https://api.github.com/repos/%s/git/trees/HEAD?recursive=1" % info["repo"]))
    if tree.get("truncated"):
        raise OSError(_("elenco file incompleto"))
    files = {x["path"]: x.get("size", 0) for x in tree["tree"] if x["type"] == "blob"}
    raw = "https://raw.githubusercontent.com/%s/HEAD/" % info["repo"]

    def get(path):
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_fetch(raw + urllib.parse.quote(path)))

    defs = [p for p in files if p.lower().endswith((".sfz", ".txt")) and
            not any(x in p for x in info.get("exclude", ()))]
    with ThreadPoolExecutor(16) as ex:
        list(ex.map(get, defs))
    audio = {p for p in files if p.lower().endswith((".wav", ".flac"))}
    needed = sorted(_needed_samples(dict(info, rr=None) if full else info, dest, audio))
    total = sum(files[p] for p in needed)
    term.note(_("%d campioni, %d MB") % (len(needed), total >> 20))
    done = [0, 0]

    def get_sample(path):
        get(path)
        with lock:
            done[0] += 1
            done[1] += files[path]
            progress(done[1], total, (done[0], len(needed)))

    lock = threading.Lock()
    with ThreadPoolExecutor(16) as ex:
        list(ex.map(get_sample, needed))
    if progress is print_progress:
        print()


def install(name, force=False, full=False, progress=print_progress):
    """progress(fatti, totale, (file, file_totali) | None): byte scaricati, chiamata dal thread del download."""
    info = PACKS[name]
    if is_installed(name) and not force:
        term.row(term.OK, name, _("già installato"), _(info["title"]).split(" — ")[0])
        return
    size = info["size_mb"] if full else info.get("light_mb", info["size_mb"])
    term.row(term.DOWN, name, term.paint(term.PURPLE, _("scarico ~%d MB") % size), _(info["title"]).split(" — ")[0])
    term.note("%s · %s" % (info["author"], _(info["license"])))
    dest = pack_dir(name)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    zips = []
    if info.get("repo"):
        # file per file da raw.githubusercontent: gli zip di GitHub applicano le conversioni
        # di fine riga di .gitattributes anche ai WAV (succede con black-and-green-guitars)
        try:
            _install_selective(name, info, dest, full, progress)
        except (OSError, ValueError) as e:
            shutil.rmtree(dest, ignore_errors=True)
            raise SongError(_("download di '%s' non riuscito: %s. Riprova più tardi.") % (name, e))
    else:
        zips = _install_zip(name, info, dest, progress)
    _finish(name, info, dest, zips)


def _install_zip(name, info, dest, progress):
    sources = info.get("urls") or [(name + ".zip", "https://github.com/%s/archive/HEAD.zip" % info["repo"])]
    zips = []
    for fname, url in sources:
        zpath = cache_dir() / fname
        if not zpath.is_file():
            term.note(url)
            _download(url, zpath, progress)
        zips.append(zpath)
    term.note(_("estraggo..."))
    for zpath in zips:
        for filename, is_dir, opener in _archive_members(zpath):
            rel = filename.split("/", 1)[1] if "/" in filename else ""
            if not rel or is_dir or filename.startswith("__MACOSX"):
                continue
            if any(x in rel for x in info.get("exclude", ())):
                continue
            if info.get("include") and not any(x in rel for x in info["include"]):
                continue
            target = dest / (rel.rsplit("/", 1)[-1].replace(" ", "_") if info.get("flatten") else rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            with opener() as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    return zips


def _archive_members(path):
    """(nome, è_cartella, apri) per ogni voce di uno zip o di un tar (.tar.xz, .tar.gz...)."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for m in z.infolist():
                yield m.filename, m.is_dir(), lambda m=m: z.open(m)
    else:
        with tarfile.open(path) as t:
            for m in t:
                yield m.name, not m.isfile(), lambda m=m: t.extractfile(m)


def _finish(name, info, dest, zips):
    flacs = list(dest.rglob("*.flac"))
    if flacs:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise SongError(_("serve ffmpeg per convertire i campioni FLAC (vedi README)"))
        term.note(_("converto %d campioni FLAC...") % len(flacs))
        with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
            list(ex.map(lambda f: _flac_to_wav(ffmpeg, f), flacs))
    (dest / ".installed").write_text("%s\n%s\n" % (info.get("repo") or info["urls"][0][1], info["license"]))
    for zpath in zips:
        zpath.unlink()
    term.row(term.OK, name, term.paint(term.GREEN, _("installato")), str(dest))


def disk_mb(name):
    d = pack_dir(name)
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 2 ** 20 if d.exists() else 0


def remove(name):
    d = pack_dir(name)
    if not d.exists():
        term.row(term.OFF, name, _("non installato"))
        return
    mb = disk_mb(name)
    shutil.rmtree(d)
    term.row(term.OK, name, _("rimosso"), _("%.0f MB liberati") % mb)


def status():
    rows = []
    for name, info in PACKS.items():
        state = _("installato %4.0f MB") % disk_mb(name) if is_installed(name) else _("mancante")
        rows.append((name, state, _(info["title"]), _(info["license"])))
    return rows
