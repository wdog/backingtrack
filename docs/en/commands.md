# ⌨️ Command reference

<!-- nav -->
<p align="center">
  <a href="../../README.md">🏠 Home</a> ·
  <a href="installation.md">📦 Installation</a> ·
  <a href="gui.md">🖥️ Graphical editor</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="format.md">📝 Song format</a> ·
  <a href="grooves.md">🥁 Grooves</a> ·
  <a href="songs.md">📚 Songs</a> ·
  <b>⌨️ Commands</b> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="development.md">⚙️ Development</a>
</p>
<p align="center"><b>🇬🇧 English</b> · <a href="../it/comandi.md">🇮🇹 Italiano</a></p>
<!-- /nav -->

```
backingtrack <file.yaml>                  shortcut for "render"
backingtrack render <file.yaml>... [options]
    -o, --out PATH       output without extension (with several files: folder). Default out/<name>
    -t, --tempo BPM      change the tempo
    -g, --groove NAME    force one groove for all sections
    --transpose N        transpose by N semitones
    --bass               add the double bass
    --mute guitar,drums  leave instruments out of the audio
    --mp3                also write the mp3
    --stems              save separate guitar.wav, drums.wav, bass.wav
    --midi-only          MIDI file only
    --dry-run            show the structure without writing files
backingtrack setup [packs] [--bass] [--full] [--force]
                                           download the samples (default: gretsch drums cabs)
backingtrack remove <pack>...              delete samples and free space
backingtrack update [--ref TAG] [--src DIR]
                                           update the program and the missing samples
backingtrack gui [file.yaml]               graphical editor (also: backingtrack-gui)
backingtrack grooves                       list the grooves
backingtrack new <file.yaml>               create a starter song file
backingtrack doctor                        full diagnostics, with what to do if something is missing
```

Messages follow the system language (Italian if it starts with `it`, English otherwise). Force it with
`BACKINGTRACK_LANG=en` or `BACKINGTRACK_LANG=it`, e.g. `BACKINGTRACK_LANG=en backingtrack doctor`.

<!-- foot -->
---

<p align="center"><a href="songs.md">⬅ Previous: 📚 Songs</a> · <a href="#">⬆ Back to top</a> · <a href="faq.md">Next: ❓ FAQ ➡</a></p>
<!-- /foot -->
