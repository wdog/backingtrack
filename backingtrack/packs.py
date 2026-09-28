"""Pacchetti di campioni (SFZ): download, estrazione e conversione, una volta sola."""
import os
import platform
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
        exclude=("Samples/black/", "GUI/"), default=True),
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
        exclude=("arco/",)),
    "epiphone": dict(
        title="Emilyguitar — Epiphone solid body (alternativa: guitar: epiphone)",
        author="Karoryfer Samples / D. Smolken", license="CC0-1.0",
        repo="sfzinstruments/karoryfer.emilyguitar", sfz="emily_clean.sfz", size_mb=100, light_mb=40, rr=1,
        keys=range(36, 90)),
}
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
        raise SongError("campioni '%s' non installati. Esegui:  backingtrack setup%s" % (name, hint))
    rel = PACKS[name].get(key)
    return pack_dir(name) / rel if rel else None


def _download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "backingtrack"})
    with urllib.request.urlopen(req) as r, open(tmp, "wb") as f:
        done = 0
        while True:
            chunk = r.read(1 << 17)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            sys.stdout.write("\r  scaricati %d MB" % (done >> 20))
            sys.stdout.flush()
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


def _install_selective(name, info, dest, full=False):
    """Scarica solo definizioni SFZ e campioni necessari, file per file."""
    import json
    tree = json.loads(_fetch("https://api.github.com/repos/%s/git/trees/HEAD?recursive=1" % info["repo"]))
    if tree.get("truncated"):
        raise OSError("elenco file incompleto")
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
    print("  %d campioni, %d MB" % (len(needed), total >> 20))
    done = [0, 0]

    def get_sample(path):
        get(path)
        done[0] += 1
        done[1] += files[path]
        sys.stdout.write("\r  scaricati %d/%d (%d MB)" % (done[0], len(needed), done[1] >> 20))
        sys.stdout.flush()

    with ThreadPoolExecutor(16) as ex:
        list(ex.map(get_sample, needed))
    print()


def install(name, force=False, full=False):
    info = PACKS[name]
    if is_installed(name) and not force:
        print("✓ %s già installato" % name)
        return
    size = info["size_mb"] if full else info.get("light_mb", info["size_mb"])
    print("↓ %s: %s (%s, %s, ~%d MB)" % (name, info["title"], info["author"], info["license"], size))
    dest = pack_dir(name)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    zips = []
    if info.get("repo"):
        # file per file da raw.githubusercontent: gli zip di GitHub applicano le conversioni
        # di fine riga di .gitattributes anche ai WAV (succede con black-and-green-guitars)
        try:
            _install_selective(name, info, dest, full)
        except (OSError, ValueError) as e:
            shutil.rmtree(dest, ignore_errors=True)
            raise SongError("download di '%s' non riuscito: %s. Riprova più tardi." % (name, e))
    else:
        zips = _install_zip(name, info, dest)
    _finish(name, info, dest, zips)


def _install_zip(name, info, dest):
    sources = info.get("urls") or [(name + ".zip", "https://github.com/%s/archive/HEAD.zip" % info["repo"])]
    zips = []
    for fname, url in sources:
        zpath = cache_dir() / fname
        if not zpath.is_file():
            print("  %s" % url)
            _download(url, zpath)
        zips.append(zpath)
    print("  estraggo...")
    for zpath in zips:
        with zipfile.ZipFile(zpath) as z:
            for member in z.infolist():
                rel = member.filename.split("/", 1)[1] if "/" in member.filename else ""
                if not rel or member.is_dir() or member.filename.startswith("__MACOSX"):
                    continue
                if any(x in rel for x in info.get("exclude", ())):
                    continue
                if info.get("include") and not any(x in rel for x in info["include"]):
                    continue
                target = dest / (rel.rsplit("/", 1)[-1].replace(" ", "_") if info.get("flatten") else rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
    return zips


def _finish(name, info, dest, zips):
    flacs = list(dest.rglob("*.flac"))
    if flacs:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise SongError("serve ffmpeg per convertire i campioni FLAC (vedi README)")
        print("  converto %d campioni FLAC..." % len(flacs))
        with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
            list(ex.map(lambda f: _flac_to_wav(ffmpeg, f), flacs))
    (dest / ".installed").write_text("%s\n%s\n" % (info.get("repo") or info["urls"][0][1], info["license"]))
    for zpath in zips:
        zpath.unlink()
    print("✓ %s installato in %s" % (name, dest))


def disk_mb(name):
    d = pack_dir(name)
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 2 ** 20 if d.exists() else 0


def remove(name):
    d = pack_dir(name)
    if not d.exists():
        print("· %s non installato" % name)
        return
    mb = disk_mb(name)
    shutil.rmtree(d)
    print("✓ %s rimosso (%.0f MB liberati)" % (name, mb))


def status():
    rows = []
    for name, info in PACKS.items():
        state = "installato %4.0f MB" % disk_mb(name) if is_installed(name) else "mancante"
        rows.append((name, state, info["title"], info["license"]))
    return rows
