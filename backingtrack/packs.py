"""Pacchetti di campioni (SFZ): download, estrazione e conversione, una volta sola."""
import os
import platform
import shutil
import subprocess
import sys
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
    "guitar": dict(
        title="Emilyguitar — Epiphone elettrica, 4 dinamiche, 3 round robin",
        author="Karoryfer Samples / D. Smolken", license="CC0-1.0",
        repo="sfzinstruments/karoryfer.emilyguitar", sfz="emily_clean.sfz", size_mb=104),
    "drums": dict(
        title="Salamander Drumkit — batteria acustica, fino a 20 round robin",
        author="Alexander Holm", license="CC-BY-SA-3.0",
        repo="studiorack/salamander-drumkit", sfz="Salamander Drumkit.sfz", size_mb=270,
        drum_map=SALAMANDER_MAP),
    "bass": dict(
        title="Contrabbasso Rubner 1958 pizzicato (opzionale, per --bass)",
        author="D. Smolken", license="CC0-1.0",
        repo="sfzinstruments/dsmolken.double-bass", sfz="d_smolken_rubner_bass_pizz.sfz", size_mb=265,
        exclude=("arco/",), optional=True),
}


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


def sfz_path(name):
    if not is_installed(name):
        hint = " --bass" if name == "bass" else ""
        raise SongError("campioni '%s' non installati. Esegui:  backingtrack setup%s" % (name, hint))
    return pack_dir(name) / PACKS[name]["sfz"]


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
    subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(flac), "-c:a", "pcm_s24le", str(wav)],
                   check=True, stdin=subprocess.DEVNULL)
    flac.unlink()


def install(name, force=False):
    info = PACKS[name]
    if is_installed(name) and not force:
        print("✓ %s già installato" % name)
        return
    print("↓ %s: %s (%s, %s)" % (name, info["title"], info["author"], info["license"]))
    zpath = cache_dir() / (name + ".zip")
    if not zpath.is_file():
        url = "https://github.com/%s/archive/HEAD.zip" % info["repo"]
        print("  %s (~%d MB)" % (url, info["size_mb"]))
        _download(url, zpath)
    dest = pack_dir(name)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    print("  estraggo...")
    with zipfile.ZipFile(zpath) as z:
        for member in z.infolist():
            rel = member.filename.split("/", 1)[1] if "/" in member.filename else ""
            if not rel or member.is_dir() or any(x in rel for x in info.get("exclude", ())):
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    flacs = list(dest.rglob("*.flac"))
    if flacs:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise SongError("serve ffmpeg per convertire i campioni FLAC (vedi README)")
        print("  converto %d campioni FLAC..." % len(flacs))
        with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
            list(ex.map(lambda f: _flac_to_wav(ffmpeg, f), flacs))
    (dest / ".installed").write_text("%s\n%s\n" % (info["repo"], info["license"]))
    zpath.unlink()
    print("✓ %s installato in %s" % (name, dest))


def status():
    rows = []
    for name, info in PACKS.items():
        rows.append((name, "installato" if is_installed(name) else "mancante", info["title"], info["license"]))
    return rows
