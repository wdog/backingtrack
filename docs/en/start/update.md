# Updating

```sh
backingtrack update
```

Downloads **only the missing samples** (the ones already there stay put, no useless downloads)
and then updates the program from GitHub, keeping GUI support. At the end it shows the version change (`1.3.0 → 1.4.0`).
Running the installer again does the same, and it says which version it is installing.

| Command | What it does |
|---|---|
| `backingtrack update` | update to the `main` version |
| `backingtrack update --ref v1.4.0` | install a specific branch or tag |
| `backingtrack update --src ~/backingtrack` | update from a local copy: handy to test changes before publishing them |

If you work on the code (folder with `.git`), `update` reminds you to use `git pull` and only handles the samples.

### Testing a local copy (before publishing)

From the project folder you can reinstall everything **as a user would get it**, without going through GitHub:

```sh
cd ~/Workspace/tracks                       # the project folder
pipx uninstall backingtrack                 # removes the current install (samples stay)
BT_SRC="$PWD" bash install.sh               # full installer, but from the local code
backingtrack doctor
```

Samples already downloaded are skipped. To test the first download from scratch too, delete them first:
`rm -rf ~/.local/share/backingtrack ~/.cache/backingtrack` (then ~460 MB to download again).

To work on the code without reinstalling at every change: `pipx install -e --system-site-packages .`
(editable: the command uses the files in the folder directly).

## Uninstalling

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
