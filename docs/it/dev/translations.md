# Traduzioni

I testi sono scritti in italiano nel codice e avvolti in `_()` (`backingtrack/i18n.py`); le traduzioni inglesi stanno in
`backingtrack/locale_en.py` (`EN` per i testi, `GROOVES_EN` per le descrizioni dei groove). Le costanti di modulo (la
guida F1, le descrizioni delle scale…) restano grezze e si traducono dove vengono mostrate. Un test fallisce se un testo
non ha la traduzione o se i segnaposto `%s` non coincidono. La documentazione sta in `docs/it/` e `docs/en/`;
`python3 docs/make_docs.py` rigenera dai dati le tabelle di groove e brani e la barra di navigazione di ogni pagina.
