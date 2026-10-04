# Installazione, aggiornamento e diagnosi



## Installazione con un comando

**Linux / macOS**

```sh
curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash
```

**Windows** (PowerShell)

```powershell
irm https://raw.githubusercontent.com/wdog/backingtrack/main/install.ps1 | iex
```

Lo script controlla Python, installa ffmpeg se manca (chiedendo conferma), installa `backingtrack`
(con `pipx` se c'è, altrimenti in un virtualenv dedicato), su Linux aggiunge la voce nel menu applicazioni
(file `.desktop` e icona in `~/.local/share`) e scarica i campioni.
**Rilanciarlo equivale ad aggiornare**: reinstalla il programma e scarica solo i campioni che mancano.
Opzioni: `BT_BASS=1` aggiunge il contrabbasso, `BT_NO_SAMPLES=1` salta i campioni, `BT_YES=1` non fa domande.

```sh
curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | BT_BASS=1 bash
```

## Installazione manuale

### 1. ffmpeg

| Sistema | Comando |
|---|---|
| 🐧 Debian / Ubuntu | `sudo apt install ffmpeg python3-pip` |
| 🐧 Fedora | `sudo dnf install ffmpeg` |
| 🐧 Arch | `sudo pacman -S ffmpeg` |
| 🍎 macOS | `brew install ffmpeg` |
| 🪟 Windows | `winget install Gyan.FFmpeg` oppure `choco install ffmpeg` |

Per l'**editor grafico** (opzionale) servono anche GTK 4 e libadwaita con i binding Python:

| Sistema | Comando |
|---|---|
| 🐧 Debian / Ubuntu | `sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1` |
| 🐧 Fedora | `sudo dnf install python3-gobject gtk4 libadwaita` |
| 🐧 Arch | `sudo pacman -S python-gobject gtk4 libadwaita` |
| 🍎 macOS | `brew install pygobject3 gtk4 libadwaita` |

### 2. backingtrack

```sh
git clone https://github.com/wdog/backingtrack.git
cd backingtrack
pipx install --system-site-packages .     # oppure: pip install .
```

`--system-site-packages` permette al programma di vedere GTK installato dal sistema: senza, la riga di comando
funziona ma `backingtrack gui` no.

Senza installare niente puoi anche usare `python3 -m backingtrack` dalla cartella del progetto
(servono `pip install numpy pyyaml`).

### 3. Campioni (una volta sola)

```sh
backingtrack setup          # 2 chitarre + batteria + casse: ~460 MB
backingtrack setup --bass   # aggiunge il contrabbasso: ~56 MB
backingtrack doctor         # cosa è installato e quanto spazio occupa
```
