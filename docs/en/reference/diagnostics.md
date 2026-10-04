# Diagnostics

```sh
backingtrack doctor
```

```
╭──────────────────────────────────────────────────────────────╮
│  ♪ backingtrack 1.3.0  ·  diagnostics                        │
╰──────────────────────────────────────────────────────────────╯

◆ Program ──────────────────────────────────────────────────────
  ✓ version     1.3.0
  ✓ installed   pipx (~/.local/share/pipx/venvs/backingtrack)
  ✓ python      3.12.3

◆ Dependencies ─────────────────────────────────────────────────
  ✓ ffmpeg      6.1.1
  ✓ numpy       1.26.4
  ✓ PyYAML      6.0.1
  ✓ GUI         GTK 4.14 · libadwaita 1.5  backingtrack gui

◆ Samples ───────────────────────────────────────── 321 MB total
      ~/.local/share/backingtrack/packs
  ✓ gretsch     ━━━━━━━━  175 MB  Black & Green Guitars  376 files
  ✓ drums       ━━━━━━━─  144 MB  Salamander Drumkit  209 files
  ✓ cabs        ────────    2 MB  Jester's Emerald + Brutal IR  21 files
  · bass        not installed  Rubner 1958 double bass, pizzicato (for --bass)

╭──────────────────────────────────────────────────────────────╮
│  ✓ All set! 🎸                                               │
│  try:  backingtrack examples/blues/sweet_home_chicago.yaml   │
╰──────────────────────────────────────────────────────────────╯
```

It checks the program, the dependencies (GUI included) and the samples, **re-reads a few random files** to catch
damaged samples and shows the folders in use. If something is wrong, it ends with a numbered list of **what to do**,
with the right command for your system.

Messages are in English; set `BACKINGTRACK_LANG=it` for Italian.
