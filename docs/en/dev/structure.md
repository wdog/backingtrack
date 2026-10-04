# Project structure

```
backingtrack/
├── backingtrack/
│   ├── cli.py         # commands
│   ├── gui.py         # GTK 4 / libadwaita graphical editor
│   ├── songfile.py    # editor model: validation, progression templates, YAML
│   ├── i18n.py        # language: _(), English by default, editor preference
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
├── examples/          # example songs (blues, rock, rockabilly, country, bluegrass, jazz)
├── docs/              # it/ and en/ documentation, images, make_docs.py, make_images.py
├── tests/             # python -m unittest discover tests
├── install.sh         # Linux/macOS installer
├── install.ps1        # Windows installer
└── pyproject.toml
```
