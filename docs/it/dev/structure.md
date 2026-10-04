# Struttura del progetto

```
backingtrack/
├── backingtrack/
│   ├── cli.py         # comandi
│   ├── gui.py         # editor grafico GTK 4 / libadwaita
│   ├── songfile.py    # modello dell'editor: validazione, modelli di giro, YAML
│   ├── i18n.py        # lingua: _(), inglese predefinito, preferenza dell'editor
│   ├── locale_en.py   # traduzioni inglesi
│   ├── data/          # icona dell'app
│   ├── song.py        # lettura YAML, battute, arrangement
│   ├── theory.py      # accordi, voicing sulle corde, scale, CAGED, scale suggerite
│   ├── grooves.py     # pattern di chitarra e batteria
│   ├── arranger.py    # accordi → note (pennate, swing, fill, umanizzazione)
│   ├── sfz.py         # lettore SFZ e WAV
│   ├── render.py      # sampler numpy
│   ├── mixer.py       # ampli, EQ, riverbero, loudness (ffmpeg)
│   ├── packs.py       # download selettivo dei campioni
│   └── midi.py        # export MIDI
├── examples/          # brani di esempio (blues, rock, rockabilly, country, bluegrass, jazz)
├── docs/              # documentazione it/ ed en/, immagini, make_docs.py, make_images.py
├── tests/             # python -m unittest discover tests
├── install.sh         # installer Linux/macOS
├── install.ps1        # installer Windows
└── pyproject.toml
```
