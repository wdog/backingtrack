# 🖥️ Riferimento comandi

<!-- nav -->
<p align="center">
  <a href="../../README.it.md">🏠 Home</a> ·
  <a href="installazione.md">📦 Installazione</a> ·
  <a href="gui.md">🖥️ Editor grafico</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="formato.md">📝 Formato</a> ·
  <a href="groove.md">🥁 Groove</a> ·
  <a href="brani.md">📚 Brani</a> ·
  <b>⌨️ Comandi</b> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="sviluppo.md">⚙️ Sviluppo</a>
</p>
<p align="center"><b>🇮🇹 Italiano</b> · <a href="../en/commands.md">🇬🇧 English</a></p>
<!-- /nav -->

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

I messaggi seguono la lingua del sistema (italiano se inizia con `it`, altrimenti inglese). Per sceglierla:
`BACKINGTRACK_LANG=it` o `BACKINGTRACK_LANG=en`, es. `BACKINGTRACK_LANG=en backingtrack doctor`.

<!-- foot -->
---

<p align="center"><a href="brani.md">⬅ Precedente: 📚 Brani</a> · <a href="#">⬆ Inizio pagina</a> · <a href="faq.md">Successiva: ❓ FAQ ➡</a></p>
<!-- /foot -->
