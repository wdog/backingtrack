# 📦 Installation, updates and diagnostics

<!-- nav -->
<p align="center">
  <a href="../../README.md">🏠 Home</a> ·
  <b>📦 Installation</b> ·
  <a href="gui.md">🖥️ Graphical editor</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="format.md">📝 Song format</a> ·
  <a href="grooves.md">🥁 Grooves</a> ·
  <a href="songs.md">📚 Songs</a> ·
  <a href="commands.md">⌨️ Commands</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="development.md">⚙️ Development</a>
</p>
<p align="center"><b>🇬🇧 English</b> · <a href="../it/installazione.md">🇮🇹 Italiano</a></p>
<!-- /nav -->

## ⚡ One-command install

**Linux / macOS**

```sh
curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash
```

**Windows** (PowerShell)

```powershell
irm https://raw.githubusercontent.com/wdog/backingtrack/main/install.ps1 | iex
```

The script checks Python, installs ffmpeg if missing (asking first), installs `backingtrack`
(with `pipx` if available, otherwise in a dedicated virtualenv), adds an entry to the application menu on Linux
(`.desktop` file and icon in `~/.local/share`) and downloads the samples.
**Running it again means updating**: it reinstalls the program and downloads only the missing samples.
Options: `BT_BASS=1` adds the double bass, `BT_NO_SAMPLES=1` skips the samples, `BT_YES=1` asks no questions.

```sh
curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | BT_BASS=1 bash
```

## 🔧 Manual install

### 1. ffmpeg

| System | Command |
|---|---|
| 🐧 Debian / Ubuntu | `sudo apt install ffmpeg python3-pip` |
| 🐧 Fedora | `sudo dnf install ffmpeg` |
| 🐧 Arch | `sudo pacman -S ffmpeg` |
| 🍎 macOS | `brew install ffmpeg` |
| 🪟 Windows | `winget install Gyan.FFmpeg` or `choco install ffmpeg` |

The **graphical editor** (optional) also needs GTK 4 and libadwaita with their Python bindings:

| System | Command |
|---|---|
| 🐧 Debian / Ubuntu | `sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1` |
| 🐧 Fedora | `sudo dnf install python3-gobject gtk4 libadwaita` |
| 🐧 Arch | `sudo pacman -S python-gobject gtk4 libadwaita` |
| 🍎 macOS | `brew install pygobject3 gtk4 libadwaita` |

### 2. backingtrack

```sh
git clone https://github.com/wdog/backingtrack.git
cd backingtrack
pipx install --system-site-packages .     # or: pip install .
```

`--system-site-packages` lets the program see the GTK installed by your system: without it the command line
works but `backingtrack gui` does not.

Without installing anything you can also run `python3 -m backingtrack` from the project folder
(it needs `pip install numpy pyyaml`).

### 3. Samples (only once)

```sh
backingtrack setup          # guitar + drums + cabinets: ~300 MB
backingtrack setup --bass   # adds the double bass: ~56 MB
backingtrack doctor         # what is installed and how much space it takes
```

## 💾 Why ~300 MB?

A realistic sound comes from **real recordings**: every guitar note and every drum hit is a separate audio file,
recorded at several dynamics (soft, medium, loud) and several times (the *round robins*, so two hits in a row are
never identical). The program itself is under 200 KB: the space is all samples.

`setup` **does not download whole libraries**: it reads the SFZ maps and takes **only the samples the program uses**,
with at most 2 round robins for the guitar and 6 for the drums. Compared to the full libraries the download goes from
~1.2 GB to ~300 MB.

| Pack | Contents | `setup` | `setup --full` |
|---|---|---|---|
| `gretsch` 🎸 | Gretsch Anniversary: normal notes + staccato, E2–E6 | ~175 MB | ~270 MB |
| `drums` 🥁 | Salamander Drumkit: kick, snare, hi-hat, toms, ride, crash | ~120 MB (stored ~145 MB) | ~185 MB |
| `cabs` 🔈 | 21 impulse responses of Marshall 4×12 cabinets | ~5 MB | ~5 MB |
| `bass` 🎻 | pizzicato double bass (only with `--bass`) | ~56 MB | ~130 MB |
| `epiphone` 🎸 | alternative guitar, Epiphone solid body (optional) | ~40 MB | ~100 MB |
| `fender` 🎸 | Fender solid body DI, bridge pickup: rock and hard rock with `amp: crunch`/`high` (optional) | ~160 MB | ~314 MB |
| `acoustic` 🎸 | Seagull steel-string acoustic guitar, played without amp (optional, GPL with exception) | ~25 MB | ~25 MB |
| `ebass` 🎸 | Black & Blue 'darkblack' electric bass, fingered (optional) | ~80 MB | ~160 MB |
| `sneakybass` 🎻 | Sneakybass double bass, light pizzicato (optional) | ~63 MB | ~124 MB |

- **Want the best?** `backingtrack setup --full` downloads every round robin: more variety, about twice the space.
- **Need space back?** `backingtrack remove bass` (or any pack); to delete everything remove the samples folder.
- **Where do they go?** `~/.local/share/backingtrack` (Linux), `~/Library/Application Support/backingtrack` (macOS)
  or `%LOCALAPPDATA%\backingtrack` (Windows). Change the folder with the `BACKINGTRACK_HOME` variable
  (e.g. an external drive).
- Downloaded **only once**: afterwards the program works offline.

## 🔄 Updating

```sh
backingtrack update
```

Downloads **only the missing samples** (the ones already there stay put, no useless downloads)
and then updates the program from GitHub, keeping GUI support. Running the installer again does the same.

| Command | What it does |
|---|---|
| `backingtrack update` | update to the `main` version |
| `backingtrack update --ref v1.2.0` | install a specific branch or tag |
| `backingtrack update --src ~/backingtrack` | update from a local copy: handy to test changes before publishing them |

If you work on the code (folder with `.git`), `update` reminds you to use `git pull` and only handles the samples.

### 🧪 Testing a local copy (before publishing)

From the project folder you can reinstall everything **as a user would get it**, without going through GitHub:

```sh
cd ~/Workspace/tracks                       # the project folder
pipx uninstall backingtrack                 # removes the current install (samples stay)
BT_SRC="$PWD" bash install.sh               # full installer, but from the local code
backingtrack doctor
```

Samples already downloaded are skipped. To test the first download from scratch too, delete them first:
`rm -rf ~/.local/share/backingtrack ~/.cache/backingtrack` (then ~300 MB to download again).

To work on the code without reinstalling at every change: `pipx install -e --system-site-packages .`
(editable: the command uses the files in the folder directly).

## 🩺 Diagnostics

```sh
backingtrack doctor
```

```
♪ backingtrack 1.2.0  — diagnostics

Program
  ✓ version      1.2.0
  ✓ installed    pipx (~/.local/share/pipx/venvs/backingtrack)
  ✓ python       3.12.3

Dependencies
  ✓ ffmpeg       6.1.1
  ✓ numpy        1.26.4
  ✓ PyYAML       6.0.1
  ✓ GUI          GTK 4.14 · libadwaita 1.5  backingtrack gui

Samples  ~/.local/share/backingtrack/packs
  ✓ gretsch        175 MB  Black & Green Guitars  376 files
  ✓ drums          144 MB  Salamander Drumkit  209 files
  ✓ cabs             2 MB  Jester's Emerald + Brutal IR  21 files
  · bass         not installed  optional: backingtrack setup bass
    total        321 MB

All set! 🎸
```

It checks the program, the dependencies (GUI included) and the samples, **re-reads a few random files** to catch
damaged samples and shows the folders in use. If something is wrong, it ends with a numbered list of **what to do**,
with the right command for your system.

The language of messages follows your system; force it with `BACKINGTRACK_LANG=en` or `BACKINGTRACK_LANG=it`.

## 🗑️ Uninstalling

The program and the samples live in different places: you can remove one, the other or both.

```sh
# 1. the program
pipx uninstall backingtrack                       # if installed with pipx (or with the installer and pipx)
rm -rf ~/.local/share/backingtrack/venv ~/.local/bin/backingtrack   # if installed by the installer without pipx
rm -f ~/.local/share/applications/io.github.wdog.backingtrack.desktop \
      ~/.local/share/icons/hicolor/256x256/apps/io.github.wdog.backingtrack.png   # menu entry (Linux)

# 2. samples, drafts and cache
rm -rf ~/.local/share/backingtrack ~/.cache/backingtrack
```

| System | Data folder (samples, draft) | Cache folder |
|---|---|---|
| 🐧 Linux | `~/.local/share/backingtrack` | `~/.cache/backingtrack` |
| 🍎 macOS | `~/Library/Application Support/backingtrack` | `~/Library/Caches/backingtrack` |
| 🪟 Windows | `%LOCALAPPDATA%\backingtrack\data` (and `\venv`) | `%LOCALAPPDATA%\backingtrack\cache` |

On Windows also remove `%LOCALAPPDATA%\backingtrack\venv\Scripts` from the user's PATH variable.
To free space without uninstalling: `backingtrack remove bass` (or another pack).

<!-- foot -->
---

<p align="center"><a href="#">⬆ Back to top</a> · <a href="gui.md">Next: 🖥️ Graphical editor ➡</a></p>
<!-- /foot -->
