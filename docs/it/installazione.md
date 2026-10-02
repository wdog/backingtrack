# 📦 Installazione, aggiornamento e diagnosi

<!-- nav -->
<p align="center">
  <a href="../../README.it.md">🏠 Home</a> ·
  <b>📦 Installazione</b> ·
  <a href="gui.md">🖥️ Editor grafico</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="formato.md">📝 Formato</a> ·
  <a href="groove.md">🥁 Groove</a> ·
  <a href="brani.md">📚 Brani</a> ·
  <a href="comandi.md">⌨️ Comandi</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="sviluppo.md">⚙️ Sviluppo</a>
</p>
<p align="center"><b>🇮🇹 Italiano</b> · <a href="../en/installation.md">🇬🇧 English</a></p>
<!-- /nav -->

## ⚡ Installazione con un comando

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

## 🔧 Installazione manuale

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
backingtrack setup          # chitarra + batteria + casse: ~300 MB
backingtrack setup --bass   # aggiunge il contrabbasso: ~56 MB
backingtrack doctor         # cosa è installato e quanto spazio occupa
```

## 💾 Perché ~300 MB?

Un suono realistico viene da **registrazioni vere**: ogni nota della chitarra e ogni colpo di batteria
sono file audio separati, registrati a più dinamiche (piano, medio, forte) e più volte (i *round robin*,
così due colpi di fila non sono mai identici). Il programma in sé pesa meno di 200 KB: lo spazio è tutto campioni.

`setup` **non scarica le librerie intere**: legge le mappe SFZ e prende **solo i campioni che il programma usa**,
e al massimo 2 round robin per la chitarra e 6 per la batteria. Rispetto alle librerie complete il download scende da ~1,2 GB a ~300 MB.

| Pacchetto | Cosa contiene | `setup` | `setup --full` |
|---|---|---|---|
| `gretsch` 🎸 | Gretsch Anniversary: note normali + staccato, E2–E6 | ~175 MB | ~270 MB |
| `drums` 🥁 | Salamander Drumkit: cassa, rullante, hi-hat, tom, ride, crash | ~120 MB (salvata ~145 MB) | ~185 MB |
| `cabs` 🔈 | 21 impulse response di casse Marshall 4×12 | ~5 MB | ~5 MB |
| `bass` 🎻 | contrabbasso pizzicato (solo con `--bass`) | ~56 MB | ~130 MB |
| `epiphone` 🎸 | chitarra alternativa, Epiphone solid body (opzionale) | ~40 MB | ~100 MB |
| `fender` 🎸 | Fender solid body DI, pickup al ponte: rock e hard rock con `amp: crunch`/`high` (opzionale) | ~160 MB | ~314 MB |
| `acoustic` 🎸 | chitarra acustica steel string Seagull, suonata senza ampli (opzionale, GPL con eccezione) | ~25 MB | ~25 MB |
| `ebass` 🎸 | basso elettrico Black & Blue 'darkblack', a dita (opzionale) | ~80 MB | ~160 MB |
| `sneakybass` 🎻 | contrabbasso Sneakybass, pizzicato leggero (opzionale) | ~63 MB | ~124 MB |

- **Vuoi il massimo?** `backingtrack setup --full` scarica tutti i round robin: più varietà, circa il doppio dello spazio.
- **Vuoi liberare spazio?** `backingtrack remove bass` (o qualsiasi pacchetto); per cancellare tutto elimina la cartella dei campioni.
- **Dove finiscono?** In `~/.local/share/backingtrack` (Linux), `~/Library/Application Support/backingtrack` (macOS)
  o `%LOCALAPPDATA%\backingtrack` (Windows). Puoi cambiare cartella con la variabile `BACKINGTRACK_HOME`
  (es. un disco esterno).
- Si scarica **una volta sola**: poi il programma funziona offline.

## 🔄 Aggiornare

```sh
backingtrack update
```

Scarica **solo i campioni che mancano** (quelli già presenti restano dove sono, niente download inutili)
e poi aggiorna il programma da GitHub, mantenendo il supporto alla GUI. In alternativa rilancia l'installer:
fa la stessa cosa.

| Comando | A cosa serve |
|---|---|
| `backingtrack update` | aggiorna alla versione `main` |
| `backingtrack update --ref v1.2.0` | installa un branch o un tag preciso |
| `backingtrack update --src ~/backingtrack` | aggiorna da una copia locale: utile per provare le modifiche prima di pubblicarle |

Se lavori sul codice (cartella con `.git`), `update` ti ricorda di usare `git pull` e si limita ai campioni.

### 🧪 Provare una copia locale (prima di pubblicare)

Dalla cartella del progetto puoi reinstallare tutto **come lo riceverebbe un utente**, senza passare da GitHub:

```sh
cd ~/Workspace/tracks                       # la cartella del progetto
pipx uninstall backingtrack                 # toglie l'installazione attuale (i campioni restano)
BT_SRC="$PWD" bash install.sh               # installer completo, ma dal codice locale
backingtrack doctor
```

I campioni già scaricati vengono saltati. Per provare anche il primo download da zero, prima cancellali:
`rm -rf ~/.local/share/backingtrack ~/.cache/backingtrack` (poi ~300 MB da riscaricare).

Per lavorare sul codice senza reinstallare a ogni modifica: `pipx install -e --system-site-packages .`
(editable: il comando usa direttamente i file della cartella).

## 🩺 Diagnosi

```sh
backingtrack doctor
```

```
♪ backingtrack 1.2.0  — diagnosi

Programma
  ✓ versione     1.2.0
  ✓ installato   pipx (~/.local/share/pipx/venvs/backingtrack)
  ✓ python       3.12.3

Dipendenze
  ✓ ffmpeg       6.1.1
  ✓ numpy        1.26.4
  ✓ PyYAML       6.0.1
  ✓ GUI          GTK 4.14 · libadwaita 1.5  backingtrack gui

Campioni  ~/.local/share/backingtrack/packs
  ✓ gretsch        175 MB  Black & Green Guitars  376 file
  ✓ drums          144 MB  Salamander Drumkit  209 file
  ✓ cabs             2 MB  Jester's Emerald + Brutal IR  21 file
  · bass         non installato  opzionale: backingtrack setup bass
    totale       321 MB

Tutto pronto! 🎸
```

Controlla programma, dipendenze (anche la GUI), campioni, **rilegge alcuni file a caso** per scoprire campioni
rovinati e mostra le cartelle usate. Se qualcosa non va, chiude con l'elenco numerato di **cosa fare**, con il comando
giusto per il tuo sistema.

I messaggi sono in inglese; per l'italiano imposta `BACKINGTRACK_LANG=it`.

## 🗑️ Disinstallare

Il programma e i campioni stanno in posti diversi: puoi togliere uno, l'altro o tutto.

```sh
# 1. il programma
pipx uninstall backingtrack                       # se installato con pipx (o con l'installer e pipx)
rm -rf ~/.local/share/backingtrack/venv ~/.local/bin/backingtrack   # se installato dall'installer senza pipx
rm -f ~/.local/share/applications/io.github.wdog.backingtrack.desktop \
      ~/.local/share/icons/hicolor/256x256/apps/io.github.wdog.backingtrack.png   # voce di menu (Linux)

# 2. i campioni, le bozze e la cache
rm -rf ~/.local/share/backingtrack ~/.cache/backingtrack
```

| Sistema | Cartella dati (campioni, bozza) | Cartella cache |
|---|---|---|
| 🐧 Linux | `~/.local/share/backingtrack` | `~/.cache/backingtrack` |
| 🍎 macOS | `~/Library/Application Support/backingtrack` | `~/Library/Caches/backingtrack` |
| 🪟 Windows | `%LOCALAPPDATA%\backingtrack\data` (e `\venv`) | `%LOCALAPPDATA%\backingtrack\cache` |

Su Windows togli anche `%LOCALAPPDATA%\backingtrack\venv\Scripts` dalla variabile PATH dell'utente.
Per liberare spazio senza disinstallare: `backingtrack remove bass` (o un altro pacchetto).

<!-- foot -->
---

<p align="center"><a href="#">⬆ Inizio pagina</a> · <a href="gui.md">Successiva: 🖥️ Editor grafico ➡</a></p>
<!-- /foot -->
