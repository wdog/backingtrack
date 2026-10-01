# 📝 Song format

<!-- nav -->
<p align="center">
  <a href="../../README.md">🏠 Home</a> ·
  <a href="installation.md">📦 Installation</a> ·
  <a href="gui.md">🖥️ Graphical editor</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <b>📝 Song format</b> ·
  <a href="grooves.md">🥁 Grooves</a> ·
  <a href="songs.md">📚 Songs</a> ·
  <a href="commands.md">⌨️ Commands</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="development.md">⚙️ Development</a>
</p>
<p align="center"><b>🇬🇧 English</b> · <a href="../it/formato.md">🇮🇹 Italiano</a></p>
<!-- /nav -->

A song is a YAML file: a few global keys and a list of sections with their chords. Section names are free text
(`Verse`, `Strofa`, `Solo`…): they are only used in `arrangement` and in the editor.

### Main keys

| Key | Default | Description |
|---|---|---|
| `title` | file name | title |
| `tempo` | `120` | BPM (30-320) |
| `groove` | `rock` | default groove ([list](grooves.md)) |
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
| `guitar` | `gretsch` | guitar: `gretsch` (hollowbody), `epiphone` (solid body), `fender` (rock/hard rock), `acoustic` (acoustic, ignores `amp`) (need `setup <name>`) |
| `amp` | from the groove | force the amp: `clean` `blues` `twang` `crunch` `high` |
| `double` | from the groove | guitar double-tracked left and right |
| `slapback` | from the groove | rockabilly slapback echo |
| `humanize` | `1.0` | 0 = perfectly in time, 2 = very "human" |
| `strum_ms` | `14` | milliseconds between one string and the next in a strum |
| `seed` | `1` | change it for different round robin and timing variations |

### Section keys

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

## 🎼 Reading a bar

Every bar has **4 beats**. The symbols written in the bar split the 4 beats **evenly**,
and the dot `.` **extends the chord before it** by one part.

Take `Em . D C`. That is 4 symbols, so each one is worth 1 beat:

| beat | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| symbol | `Em` | `.` | `D` | `C` |
| plays | **Em** | Em (held) | **D** | **C** |

So: **Em for 2 beats, D for 1, C for 1**. In the graphical editor just hover over the bar: *Em 2 beats · D 1 · C 1*,
and in the player strip Em takes half the box.

| Written | Meaning |
|---|---|
| `\| A7 \|` | A7 for the whole bar |
| `\| A7 D7 \|` | two chords: 2 beats each |
| `\| C G Am F \|` | one chord per beat |
| `\| Em . D C \|` | Em 2 beats, D 1, C 1 |
| `\| C . . G \|` | C 3 beats, G 1 |
| `\| C G F \|` | three chords: 1⅓ beats each (possible but unusual) |
| `\| % \|` | repeats the previous bar |
| `\| N.C. \|` | no guitar, the drums go on |

Common mistakes, with the message you get:

| You write | Problem | Fix |
|---|---|---|
| `. D` | the `.` extends the previous chord, so it cannot open the bar | `D` or `Em . D C` |
| `am` | the root must be uppercase | `Am` |
| `H7` | in English notation Ti is `B` | `B7` |
| `%` as first bar | there is no previous bar to repeat | write the chord |
| `A B C D E` | more than 4 symbols (one per beat at most) | split it over two bars |

## 🎸 Supported chords

Root `A`…`G` with `#` or `b`, then one of these suffixes, and an optional bass `/X` (e.g. `D/F#`):

| Type | Suffixes |
|---|---|
| major / minor | *(none)*, `m`, `min`, `-` |
| sevenths | `7`, `maj7`, `M7`, `m7`, `mmaj7`, `m7b5`, `ø`, `dim7`, `7sus4` |
| sixths and ninths | `6`, `m6`, `9`, `m9`, `maj9`, `add9`, `13` |
| altered | `7#9`, `7b9`, `7#5`, `aug`, `+`, `dim`, `°` |
| suspended | `sus2`, `sus4` |
| power chord | `5` |

<!-- foot -->
---

<p align="center"><a href="tutorial.md">⬅ Previous: 🎓 Tutorial</a> · <a href="#">⬆ Back to top</a> · <a href="grooves.md">Next: 🥁 Grooves ➡</a></p>
<!-- /foot -->
