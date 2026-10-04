# Creare un groove

Un groove è una voce del dizionario `GROOVES` in [`backingtrack/grooves.py`](https://github.com/wdog/backingtrack/blob/main/backingtrack/grooves.py) e descrive
**una battuta di 4/4**: cosa fa la chitarra, cosa fa la batteria, il basso e il suono.

```python
"funk/disco": g("Disco funk: cassa in quattro, hi-hat aperto in levare",   # descrizione (menu e --help)
                "clean",                                    # ampli: clean blues twang crunch high
                pat("dudUdudUdudUdudU", 92, 70, dur=0.22),  # chitarra: 16 caratteri = sedicesimi
                DISCO_BEAT,                                 # batteria: [(beat, nota GM, velocity)]
                FUNK_TURN,                                  # variazione ogni 4 battute
                bass="octave",                              # stile del basso
                double=True,                                # chitarra doppiata L/R
                voicing="triad"),                           # forma degli accordi
```

**Chitarra** — `pat("...")` scrive il ritmo come testo: 8 caratteri = ottavi, 12 = terzine, 16 = sedicesimi
(gli spazi si ignorano). Maiuscola = forte, minuscola = piano.

| Carattere | Colpo | Carattere | Colpo |
|---|---|---|---|
| `D` / `U` | pennata giù / su | `X` | chop (corde alte stoppate) |
| `M` / `N` | giù / su stoppate (palm mute) | `P` / `p` | power chord / power chord stoppato |
| `J` | accordo jazz a 4 note | `B` / `F` | tonica / quinta al basso |
| `.` | pausa | `-` | tiene la nota precedente |

Per i bicordi boogie c'è `boogie("55665566")` (tonica + 5a/6a/7a). In alternativa si scrive la lista degli eventi:
`(beat, tipo, velocity[, durata])`, con beat da 0 a 4 (`.5` = levare, spostato dallo swing; `T1`/`T2` = terzine).

**Batteria** — lista di `(beat, nota, velocity)` con le costanti `KICK`, `SNARE`, `STICK`, `HH`, `OHH`, `PEDAL`, `LT`,
`MT`, `HT`, `CRASH`, `RIDE`, `BELL` e gli aiuti `hat8()`, `hat16()`, `hits(nota, [beat])`. Si usano solo note
presenti nel kit Salamander (niente cowbell o clap: c'è `BELL`, la campana del ride).

**Altri parametri** di `g()`: `turn` (variazione ogni 4 battute) e `fill` (rullata di fine sezione), `bass` (`eighths`
`rootfifth` `stop` `slow` `walk` `two` `octave` `funk` `reggae` `quarters` `dotted` `tumbao`), `swing` (0–1),
`double`, `slap` (slapback), `voicing` (`barre` `open` `jazz` `triad`), `mute_len` (durata delle stoppate).

Poi: il nome col prefisso dello stile (`funk/…`) lo mette nel menu giusto della GUI; aggiungi la descrizione inglese
in `GROOVES_EN` (`backingtrack/locale_en.py`); `python3 -m unittest discover tests` controlla che tutti i groove si
arrangino senza errori e siano tradotti; `python3 docs/make_docs.py` rigenera le tabelle dei groove nelle due lingue.
Un **nuovo stile** richiede anche `STYLE_EMOJI`/`STYLE_NAMES` in `gui.py` e il logo (`docs/make_images.py`).
