# Song format

A song is a YAML file: a few global keys and a list of sections with their chords. Section names are free text
(`Verse`, `Strofa`, `Solo`…): they are only used in `arrangement` and in the editor.

## Main keys

| Key | Default | Description |
|---|---|---|
| `title` | file name | title |
| `tempo` | `120` | BPM (30-320) |
| `groove` | `rock` | default groove ([list](../grooves/index.md)) |
| `sections` | — | list of sections (required) |
| `arrangement` | section order | e.g. `[Intro, Verse x2, Chorus]` |
| `transpose` | `0` | semitones (+/-) |
| `swing` | from the groove | 0 = straight … 1 = triplet |
| `count_in` | `true` | one bar of sticks before starting |
| `ending` | `true` | final chord with cymbal |
| `ending_chord` | first chord | chord of the ending |
| `fills` | `true` | drum fill on the last bar of every section |
| `crash` | `true` | crash at the start of every section |
| `bass` | `false` | `true` = double bass, or `ebass` (electric) or `sneakybass` (needs `setup <name>`) |
| `voicing` | from the groove | shape of full chords: `barre`, `open` (first position, where it exists), `jazz` (4 notes), `triad` (3 high strings) |
| `guitar` | `fender` | guitar: `fender` (solid body), `gretsch` (hollowbody), `epiphone` (solid body), `acoustic` (acoustic, ignores `amp`) (need `setup <name>`) |
| `amp` | from the groove | force the amp: `clean` `blues` `twang` `crunch` `high` |
| `double` | from the groove | guitar double-tracked left and right |
| `slapback` | from the groove | rockabilly slapback echo |
| `humanize` | `1.0` | 0 = perfectly in time, 2 = very "human" |
| `strum_ms` | `14` | milliseconds between one string and the next in a strum |
| `seed` | `1` | change it for different round robin and timing variations |

## Section keys

| Key | Default | Description |
|---|---|---|
| `name` | `Section N` | name used in `arrangement` |
| `chords` | — | bars (required) |
| `repeat` | `1` | how many times to play it |
| `groove` | the song's | groove of the section |
| `swing` | — | swing of the section |
| `volume` | `1.0` | dynamics (e.g. `0.8` for a softer verse) |
| `fill` | `fills` | drum fill at the end of the section |
| `guitar` / `drums` | `true` | `false` to drop the instrument in the section |
