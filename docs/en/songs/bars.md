# Reading a bar

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
