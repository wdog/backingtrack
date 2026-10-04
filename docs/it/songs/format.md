# Formato della canzone

Un brano è un file YAML: poche chiavi globali e un elenco di sezioni con i loro accordi. I nomi delle sezioni sono
liberi (`Verse`, `Strofa`, `Solo`…): servono solo in `arrangement` e nell'editor.

## Chiavi principali

| Chiave | Default | Descrizione |
|---|---|---|
| `title` | nome file | titolo |
| `tempo` | `120` | BPM (30-320) |
| `groove` | `rock` | groove di default ([elenco](../grooves/index.md)) |
| `sections` | — | elenco delle sezioni (obbligatorio) |
| `arrangement` | ordine delle sezioni | es. `[Intro, Strofa x2, Rit]` |
| `transpose` | `0` | semitoni (+/-) |
| `swing` | dal groove | 0 = dritto … 1 = terzinato |
| `count_in` | `true` | una battuta di bacchette prima di partire |
| `ending` | `true` | accordo finale con piatto |
| `ending_chord` | primo accordo | accordo del finale |
| `fills` | `true` | rullata sull'ultima battuta di ogni sezione |
| `crash` | `true` | piatto all'inizio di ogni sezione |
| `bass` | `false` | `true` = contrabbasso, oppure `ebass` (elettrico) o `sneakybass` (serve `setup <nome>`) |
| `voicing` | dal groove | forma degli accordi pieni: `barre`, `open` (prima posizione, dove esiste), `jazz` (4 note), `triad` (3 corde alte) |
| `guitar` | `fender` | chitarra: `fender` (solid body), `gretsch` (hollowbody), `epiphone` (solid body), `acoustic` (acustica, ignora `amp`) (servono `setup <nome>`) |
| `amp` | dal groove | forza l'ampli: `clean` `blues` `twang` `crunch` `high` |
| `double` | dal groove | chitarra doppiata a sinistra e destra |
| `slapback` | dal groove | eco slapback rockabilly |
| `humanize` | `1.0` | 0 = perfettamente a tempo, 2 = molto "umano" |
| `strum_ms` | `14` | millisecondi tra una corda e l'altra nella pennata |
| `seed` | `1` | cambia per avere variazioni diverse di round robin e timing |

## Chiavi delle sezioni

| Chiave | Default | Descrizione |
|---|---|---|
| `name` | `Sezione N` | nome usato in `arrangement` |
| `chords` | — | battute (obbligatorio) |
| `repeat` | `1` | quante volte suonarla |
| `groove` | quello del brano | groove della sezione |
| `swing` | — | swing della sezione |
| `volume` | `1.0` | dinamica (es. `0.8` per una strofa più piano) |
| `fill` | `fills` | rullata a fine sezione |
| `guitar` / `drums` | `true` | `false` per togliere lo strumento nella sezione |
