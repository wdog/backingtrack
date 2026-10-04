# Command reference

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
                                           download the samples (default: gretsch drums cabs fender)
backingtrack remove <pack>...              delete samples and free space
backingtrack update [--ref TAG] [--src DIR]
                                           update the program and the missing samples
backingtrack gui [file.yaml]               graphical editor (also: backingtrack-gui)
backingtrack grooves                       list the grooves
backingtrack new <file.yaml>               create a starter song file
backingtrack doctor                        full diagnostics, with what to do if something is missing
```

Messages are in English; for Italian set `BACKINGTRACK_LANG=it`, e.g. `BACKINGTRACK_LANG=it backingtrack doctor`.
Add it to your shell profile to keep it: `export BACKINGTRACK_LANG=it`.
