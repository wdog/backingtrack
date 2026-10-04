# Translations

Texts are written in Italian in the code and wrapped in `_()` (`backingtrack/i18n.py`); the English translations are
in `backingtrack/locale_en.py` (`EN` for texts, `GROOVES_EN` for groove descriptions). Module-level constants (the F1
guide, scale descriptions…) stay raw and are translated where they are shown. A test fails if a text has no
translation or if its `%s` placeholders differ. The documentation lives in `docs/it/` and `docs/en/`;
`python3 docs/make_docs.py` regenerates the groove and song tables from the data and the navigation bar of every page.
