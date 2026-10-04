# Aggiornare

```sh
backingtrack update
```

Scarica **solo i campioni che mancano** (quelli già presenti restano dove sono, niente download inutili)
e poi aggiorna il programma da GitHub, mantenendo il supporto alla GUI. Alla fine mostra il cambio di versione (`1.3.0 → 1.4.0`).
In alternativa rilancia l'installer: fa la stessa cosa e dice quale versione sta installando.

| Comando | A cosa serve |
|---|---|
| `backingtrack update` | aggiorna alla versione `main` |
| `backingtrack update --ref v1.4.0` | installa un branch o un tag preciso |
| `backingtrack update --src ~/backingtrack` | aggiorna da una copia locale: utile per provare le modifiche prima di pubblicarle |

Se lavori sul codice (cartella con `.git`), `update` ti ricorda di usare `git pull` e si limita ai campioni.

### Provare una copia locale (prima di pubblicare)

Dalla cartella del progetto puoi reinstallare tutto **come lo riceverebbe un utente**, senza passare da GitHub:

```sh
cd ~/Workspace/tracks                       # la cartella del progetto
pipx uninstall backingtrack                 # toglie l'installazione attuale (i campioni restano)
BT_SRC="$PWD" bash install.sh               # installer completo, ma dal codice locale
backingtrack doctor
```

I campioni già scaricati vengono saltati. Per provare anche il primo download da zero, prima cancellali:
`rm -rf ~/.local/share/backingtrack ~/.cache/backingtrack` (poi ~460 MB da riscaricare).

Per lavorare sul codice senza reinstallare a ogni modifica: `pipx install -e --system-site-packages .`
(editable: il comando usa direttamente i file della cartella).

## Disinstallare

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
