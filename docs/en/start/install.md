# Installation, updates and diagnostics



## One-command install

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

## Manual install

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
backingtrack setup          # 2 guitars + drums + cabinets: ~460 MB
backingtrack setup --bass   # adds the double bass: ~56 MB
backingtrack doctor         # what is installed and how much space it takes
```
