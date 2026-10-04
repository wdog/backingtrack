# Why ~460 MB?

A realistic sound comes from **real recordings**: every guitar note and every drum hit is a separate audio file,
recorded at several dynamics (soft, medium, loud) and several times (the *round robins*, so two hits in a row are
never identical). The program itself is under 200 KB: the space is all samples.

`setup` **does not download whole libraries**: it reads the SFZ maps and takes **only the samples the program uses**,
with at most 2 round robins for the guitar and 6 for the drums. Compared to the full libraries the download goes from
~1.2 GB to ~460 MB.

| Pack | Contents | `setup` | `setup --full` |
|---|---|---|---|
| `gretsch` 🎸 | Gretsch Anniversary: normal notes + staccato, E2–E6 | ~175 MB | ~270 MB |
| `drums` 🥁 | Salamander Drumkit: kick, snare, hi-hat, toms, ride, crash | ~120 MB (stored ~145 MB) | ~185 MB |
| `cabs` 🔈 | 21 impulse responses of Marshall 4×12 cabinets | ~5 MB | ~5 MB |
| `bass` 🎻 | pizzicato double bass (only with `--bass`) | ~56 MB | ~130 MB |
| `epiphone` 🎸 | alternative guitar, Epiphone solid body (optional) | ~40 MB | ~100 MB |
| `fender` 🎸 | Fender solid body DI, bridge pickup: default guitar | ~160 MB | ~314 MB |
| `acoustic` 🎸 | Seagull steel-string acoustic guitar, played without amp (optional, GPL with exception) | ~25 MB | ~25 MB |
| `ebass` 🎸 | Black & Blue 'darkblack' electric bass, fingered (optional) | ~80 MB | ~160 MB |
| `sneakybass` 🎻 | Sneakybass double bass, light pizzicato (optional) | ~63 MB | ~124 MB |

- **Want the best?** `backingtrack setup --full` downloads every round robin: more variety, about twice the space.
- **Need space back?** `backingtrack remove bass` (or any pack); to delete everything remove the samples folder.
- **Where do they go?** `~/.local/share/backingtrack` (Linux), `~/Library/Application Support/backingtrack` (macOS)
  or `%LOCALAPPDATA%\backingtrack` (Windows). Change the folder with the `BACKINGTRACK_HOME` variable
  (e.g. an external drive).
- Downloaded **only once**: afterwards the program works offline.
