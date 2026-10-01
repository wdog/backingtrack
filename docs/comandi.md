# 🖥️ Riferimento comandi

[⬅ README](../README.md) · [Installazione](installazione.md) · [Editor grafico](gui.md) · [Tutorial ed esempi](tutorial.md) · [Formato](formato.md) · [Groove](groove.md) · [Brani](brani.md) · [Comandi](comandi.md) · [FAQ](faq.md) · [Sviluppo](sviluppo.md)

## 🖥️ Riferimento comandi

```
backingtrack <file.yaml>                  scorciatoia per "render"
backingtrack render <file.yaml>... [opzioni]
    -o, --out PATH       output senza estensione (con più file: cartella). Default out/<nome>
    -t, --tempo BPM      cambia il tempo
    -g, --groove NOME    forza un groove per tutte le sezioni
    --transpose N        trasponi di N semitoni
    --bass               aggiungi il contrabbasso
    --mute guitar,drums  escludi strumenti dall'audio
    --mp3                crea anche l'mp3
    --stems              salva guitar.wav, drums.wav, bass.wav separati
    --midi-only          solo il file MIDI
    --dry-run            mostra la struttura senza generare file
backingtrack setup [pacchetti] [--bass] [--full] [--force]
                                           scarica i campioni (default: gretsch drums cabs)
backingtrack remove <pacchetto>...         cancella campioni e libera spazio
backingtrack update [--ref TAG] [--src DIR]
                                           aggiorna programma e campioni mancanti
backingtrack gui [file.yaml]               editor grafico (anche: backingtrack-gui)
backingtrack grooves                       elenco dei groove
backingtrack new <file.yaml>               crea un file canzone di partenza
backingtrack doctor                        diagnosi completa, con cosa fare se manca qualcosa
```
