# Diagnosi

```sh
backingtrack doctor
```

```
╭──────────────────────────────────────────────────────────────╮
│  ♪ backingtrack 1.3.0  ·  diagnosi                           │
╰──────────────────────────────────────────────────────────────╯

◆ Programma ────────────────────────────────────────────────────
  ✓ versione    1.3.0
  ✓ installato  pipx (~/.local/share/pipx/venvs/backingtrack)
  ✓ python      3.12.3

◆ Dipendenze ───────────────────────────────────────────────────
  ✓ ffmpeg      6.1.1
  ✓ numpy       1.26.4
  ✓ PyYAML      6.0.1
  ✓ GUI         GTK 4.14 · libadwaita 1.5  backingtrack gui

◆ Campioni ──────────────────────────────────── 321 MB in totale
      ~/.local/share/backingtrack/packs
  ✓ gretsch     ━━━━━━━━  175 MB  Black & Green Guitars  376 file
  ✓ drums       ━━━━━━━─  144 MB  Salamander Drumkit  209 file
  ✓ cabs        ────────    2 MB  Jester's Emerald + Brutal IR  21 file
  · bass        non installato  Contrabbasso Rubner 1958 pizzicato (per --bass)

╭──────────────────────────────────────────────────────────────╮
│  ✓ Tutto pronto! 🎸                                          │
│  prova:  backingtrack examples/blues/sweet_home_chicago.yaml │
╰──────────────────────────────────────────────────────────────╯
```

Controlla programma, dipendenze (anche la GUI), campioni, **rilegge alcuni file a caso** per scoprire campioni
rovinati e mostra le cartelle usate. Se qualcosa non va, chiude con l'elenco numerato di **cosa fare**, con il comando
giusto per il tuo sistema.

I messaggi sono in inglese; per l'italiano imposta `BACKINGTRACK_LANG=it`.
