# 🎓 Tutorial and examples

<!-- nav -->
<p align="center">
  <a href="../../README.md">🏠 Home</a> ·
  <a href="installation.md">📦 Installation</a> ·
  <a href="gui.md">🖥️ Graphical editor</a> ·
  <b>🎓 Tutorial</b> ·
  <a href="format.md">📝 Song format</a> ·
  <a href="grooves.md">🥁 Grooves</a> ·
  <a href="songs.md">📚 Songs</a> ·
  <a href="commands.md">⌨️ Commands</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="development.md">⚙️ Development</a>
</p>
<p align="center"><b>🇬🇧 English</b> · <a href="../it/tutorial.md">🇮🇹 Italiano</a></p>
<!-- /nav -->

## 🎓 Tutorial: your first backing track

### Step 1 — create the file

```sh
backingtrack new my_song.yaml
```

This creates an example file, already commented. Open it with a text editor.

### Step 2 — tempo and groove

```yaml
title: My blues
tempo: 96          # beats per minute
groove: blues      # see "backingtrack grooves"
```

### Step 3 — write the chords

Each `|` separates one 4/4 bar. You can break lines whenever you like.

```yaml
sections:
  - name: Verse
    chords: |
      | A7 | D7 | A7 | A7 |
      | D7 | D7 | A7 | A7 |
      | E7 | D7 | A7 | E7 |
```

Two chords in the same bar split the beats: `| A7 D7 |` = 2 + 2.
A dot extends the chord: `| C . . G |` = 3 + 1.

### Step 4 — repeat the sections

```yaml
  - name: Verse
    repeat: 3        # play this section 3 times
```

Or pick the full order with `arrangement` (it overrides `repeat`):

```yaml
arrangement: [Intro, Verse x2, Solo, Verse, Outro]
```

### Step 5 — render and listen

```sh
backingtrack my_song.yaml --mp3
```

### Step 6 — customize

```sh
backingtrack my_song.yaml --tempo 80          # slower, to practice
backingtrack my_song.yaml --transpose 2       # one tone up
backingtrack my_song.yaml --groove blues/slow # try another groove
backingtrack my_song.yaml --bass              # add the double bass
backingtrack my_song.yaml --mute guitar       # drums only (you play the rhythm part)
backingtrack my_song.yaml --stems             # separate tracks
```

Tip: with `--dry-run` you check the structure instantly without rendering audio.

## 💡 Examples

### 12-bar blues with intro and solo

```yaml
title: 12-bar blues in A
tempo: 100
groove: blues

sections:
  - name: Intro
    chords: "| E7 | D7 | A7 | E7 |"      # turnaround
  - name: Verse
    repeat: 3
    chords: |
      | A7 | D7 | A7 | A7 |
      | D7 | D7 | A7 | A7 |
      | E7 | D7 | A7 | E7 |
  - name: Solo
    groove: blues/7                       # boogie with the seventh
    repeat: 2
    chords: |
      | A7 | D7 | A7 | % |
      | D7 | %  | A7 | % |
      | E7 | D7 | A7 D7 | A7 E7 |
```

### Rock song: palm-muted verse, open chorus

```yaml
title: Rock in E
tempo: 132
groove: rock                    # palm-muted power chords, double-tracked guitars

sections:
  - name: Verse
    chords: |
      | E5 | E5 | D5 A5 | E5 |
      | E5 | E5 | D5 A5 | B5 |
  - name: Chorus
    groove: rock/strum          # open chords in crunch
    chords: "| A | E | B | E |"
  - name: Bridge
    groove: rock/drive
    volume: 0.9                 # a little softer
    chords: "| C#m | A | E | B |"

arrangement: [Verse x2, Chorus x2, Verse, Chorus x2, Bridge x2, Chorus x2]
```

### Rockabilly with double bass and slapback

```yaml
title: Rockabilly in E
tempo: 172
groove: rockabilly      # boom-chick + train beat
bass: true

sections:
  - name: Verse
    repeat: 2
    chords: |
      | E | E | E | E7 |
      | A | A | E | E |
      | B7 | A7 | E | B7 |
  - name: Solo
    groove: rockabilly/boogie
    chords: |
      | E | % | % | % |
      | A | % | E | % |
      | B | A | E | B |
```

### Guitar-only intro, custom ending

```yaml
title: Ballad
tempo: 70
groove: rock/ballad
ending_chord: Gadd9     # final chord (default: the first one of the song)
count_in: false

sections:
  - name: Intro
    drums: false        # drums come in later
    chords: "| G | D/F# | Em | C |"
  - name: Verse
    repeat: 2
    chords: "| G | D/F# | Em | C | G | D | C | C |"
```

### Rest and stop

```yaml
    chords: "| A7 | A7 | N.C. | E7 |"    # N.C. = the guitar is silent for one bar
```

### Practice session

```sh
# render all the blues at 80 BPM, drums and bass only, as mp3
backingtrack render examples/blues/*.yaml --tempo 80 --mute guitar --bass --mp3 -o practice/
```

<!-- foot -->
---

<p align="center"><a href="gui.md">⬅ Previous: 🖥️ Graphical editor</a> · <a href="#">⬆ Back to top</a> · <a href="format.md">Next: 📝 Song format ➡</a></p>
<!-- /foot -->
