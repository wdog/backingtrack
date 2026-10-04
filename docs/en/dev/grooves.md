# Creating a groove

A groove is an entry of the `GROOVES` dictionary in [`backingtrack/grooves.py`](https://github.com/wdog/backingtrack/blob/main/backingtrack/grooves.py) and describes
**one 4/4 bar**: what the guitar does, what the drums do, the bass and the sound.

```python
"funk/disco": g("Disco funk: cassa in quattro, hi-hat aperto in levare",   # description (menus and --help)
                "clean",                                    # amp: clean blues twang crunch high
                pat("dudUdudUdudUdudU", 92, 70, dur=0.22),  # guitar: 16 characters = sixteenths
                DISCO_BEAT,                                 # drums: [(beat, GM note, velocity)]
                FUNK_TURN,                                  # variation every 4 bars
                bass="octave",                              # bass style
                double=True,                                # double-tracked guitar L/R
                voicing="triad"),                           # chord shape
```

**Guitar** — `pat("...")` writes the rhythm as text: 8 characters = eighths, 12 = triplets, 16 = sixteenths
(spaces are ignored). Uppercase = loud, lowercase = soft.

| Character | Hit | Character | Hit |
|---|---|---|---|
| `D` / `U` | down / up strum | `X` | chop (muted high strings) |
| `M` / `N` | muted down / up (palm mute) | `P` / `p` | power chord / muted power chord |
| `J` | 4-note jazz chord | `B` / `F` | root / fifth in the bass |
| `.` | rest | `-` | holds the previous note |

For boogie double stops there is `boogie("55665566")` (root + 5th/6th/7th). Otherwise write the event list:
`(beat, type, velocity[, length])`, with beats from 0 to 4 (`.5` = offbeat, moved by the swing; `T1`/`T2` = triplets).

**Drums** — a list of `(beat, note, velocity)` with the constants `KICK`, `SNARE`, `STICK`, `HH`, `OHH`, `PEDAL`, `LT`,
`MT`, `HT`, `CRASH`, `RIDE`, `BELL` and the helpers `hat8()`, `hat16()`, `hits(note, [beats])`. Use only notes present
in the Salamander kit (no cowbell or clap: there is `BELL`, the ride bell).

**Other parameters** of `g()`: `turn` (variation every 4 bars) and `fill` (end-of-section fill), `bass` (`eighths`
`rootfifth` `stop` `slow` `walk` `two` `octave` `funk` `reggae` `quarters` `dotted` `tumbao`), `swing` (0–1),
`double`, `slap` (slapback), `voicing` (`barre` `open` `jazz` `triad`), `mute_len` (length of muted hits).

Then: the name with the style prefix (`funk/…`) puts it in the right GUI menu; add the English description to
`GROOVES_EN` in `backingtrack/locale_en.py`; `python3 -m unittest discover tests` checks that every groove arranges
without errors and is translated; `python3 docs/make_docs.py` regenerates the groove tables in both languages.
A **new style** also needs `STYLE_EMOJI`/`STYLE_NAMES` in `gui.py` and the logo (`docs/make_images.py`).
