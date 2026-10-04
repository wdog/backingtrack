# Development

```sh
git clone git@github.com:wdog/backingtrack.git && cd backingtrack
pipx install -e --system-site-packages .        # the command uses the repo files directly
python3 -m unittest discover tests               # tests (no samples needed)
python3 -m backingtrack render examples/*/*.yaml --dry-run   # validate every example
python3 docs/make_docs.py                        # regenerate groove/song tables and the site home
```

Pipeline: `song.py` (YAML → bars) → `arranger.py` (bars → notes on 6 strings) → `render.py` + `sfz.py` (notes →
samples) → `mixer.py` (amp, cabinets, mix with ffmpeg).
