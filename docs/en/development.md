# ⚙️ How it works and project structure

<!-- nav -->
<p align="center">
  <a href="../../README.md">🏠 Home</a> ·
  <a href="installation.md">📦 Installation</a> ·
  <a href="gui.md">🖥️ Graphical editor</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="format.md">📝 Song format</a> ·
  <a href="grooves.md">🥁 Grooves</a> ·
  <a href="songs.md">📚 Songs</a> ·
  <a href="commands.md">⌨️ Commands</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <b>⚙️ Development</b>
</p>
<p align="center"><b>🇬🇧 English</b> · <a href="../it/sviluppo.md">🇮🇹 Italiano</a></p>
<!-- /nav -->

## ⚙️ How it works

<p align="center"><img src="../pipeline.jpg" alt="pipeline" width="900"></p>

1. **`song.yaml`** — describe tempo, groove and sections with their chords, bar by bar.
2. **Arranger** — turns each chord into a *voicing* on the 6 strings and applies the groove pattern:
   strums (with the real delay between one string and the next), swing, accents, fills, variations, humanization.
   The result is a list of notes, as in a MIDI file.
3. **Sampler** — for each note it picks the right sample (key, dynamics, round robin), tunes it
   and places it at the exact point of the track. A small engine written in **numpy** does it, reading
   the **SFZ** format, the open standard for sampled instruments.
4. **Mixer** — **ffmpeg** runs the "direct" (DI) guitar through an amp + cabinet chain, compresses and equalizes
   the drums, adds slapback and reverb, balances the levels and brings everything to a steady listening loudness.
5. **Output** — WAV/MP3 to listen to, MIDI to open in a DAW, stems to mix as you like.

### 🧰 Tools used and why

| Tool | Role | Why this one |
|---|---|---|
| 🐍 **Python 3.8+** | the whole program | everywhere, easy to read and change |
| 🔢 **numpy** | sampling engine, balancing, reverb | sums thousands of notes in a few seconds, nothing to compile |
| 📄 **PyYAML** | reads the song file | YAML is readable and easy to write by hand |
| 🎬 **ffmpeg** | amp, cabinet (`afir` convolution), EQ, compressors, reverb, limiter, MP3, FLAC conversion | professional audio filters in C, very fast, installable on every system |
| 🎹 **SFZ** | instrument format | open standard (text + WAV): free quality libraries with clear licenses |
| 🎸 **Black & Green Guitars** | guitar samples (Gretsch) | sampled on every semitone, with staccato; recorded direct (DI), so the amp is chosen later |
| 🔈 **Jester's IR** | guitar cabinets | impulse responses of miked Marshall 4×12s: the sound of a real cabinet, via convolution |
| 🥁 **Salamander Drumkit** | drum samples | a real acoustic kit, many dynamics and round robins: no "machine-gun effect" |

**Why not a General MIDI soundfont with fluidsynth?** That was the first version: quick to write, but GM guitars
sound fake. Here every instrument is a dedicated multisampled library, and the guitar goes through a simulated amp
as in a studio.

**Why not use an external sampler directly (sfizz, LinuxSampler)?** They are not available evenly on every system.
The built-in numpy engine reads only the subset of SFZ it needs and runs wherever Python runs.

## 🌐 Translations

Texts are written in Italian in the code and wrapped in `_()` (`backingtrack/i18n.py`); the English translations are
in `backingtrack/locale_en.py` (`EN` for texts, `GROOVES_EN` for groove descriptions). Module-level constants (the F1
guide, scale descriptions…) stay raw and are translated where they are shown. A test fails if a text has no
translation or if its `%s` placeholders differ. The documentation lives in `docs/it/` and `docs/en/`;
`python3 docs/make_docs.py` regenerates the groove and song tables from the data and the navigation bar of every page.

## 🗂️ Project structure

```
backingtrack/
├── backingtrack/
│   ├── cli.py         # commands
│   ├── gui.py         # GTK 4 / libadwaita graphical editor
│   ├── songfile.py    # editor model: validation, progression templates, YAML
│   ├── i18n.py        # language: _(), system language, editor preference
│   ├── locale_en.py   # English translations
│   ├── data/          # app icon
│   ├── song.py        # YAML reading, bars, arrangement
│   ├── theory.py      # chords, voicings on the strings, scales, CAGED, scale suggestions
│   ├── grooves.py     # guitar and drum patterns
│   ├── arranger.py    # chords → notes (strums, swing, fills, humanization)
│   ├── sfz.py         # SFZ and WAV reader
│   ├── render.py      # numpy sampler
│   ├── mixer.py       # amp, EQ, reverb, loudness (ffmpeg)
│   ├── packs.py       # selective sample download
│   └── midi.py        # MIDI export
├── examples/          # example songs (blues, rock, rockabilly, country, jazz)
├── docs/              # it/ and en/ documentation, images, make_docs.py, make_images.py
├── tests/             # python -m unittest discover tests
├── install.sh         # Linux/macOS installer
├── install.ps1        # Windows installer
└── pyproject.toml
```

<!-- foot -->
---

<p align="center"><a href="faq.md">⬅ Previous: ❓ FAQ</a> · <a href="#">⬆ Back to top</a></p>
<!-- /foot -->
