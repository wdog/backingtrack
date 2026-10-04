# Sviluppo

```sh
git clone git@github.com:wdog/backingtrack.git && cd backingtrack
pipx install -e --system-site-packages .        # il comando usa direttamente i file del repo
python3 -m unittest discover tests               # test (non servono i campioni)
python3 -m backingtrack render examples/*/*.yaml --dry-run   # valida tutti gli esempi
python3 docs/make_docs.py                        # rigenera tabelle di groove/brani e la home del sito
```

Pipeline: `song.py` (YAML → battute) → `arranger.py` (battute → note su 6 corde) → `render.py` + `sfz.py` (note →
campioni) → `mixer.py` (ampli, casse, mix con ffmpeg).
