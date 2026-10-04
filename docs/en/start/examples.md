# Examples

## 12-bar blues with intro and solo

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

## Rock song: palm-muted verse, open chorus

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

## Rockabilly with double bass and slapback

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

## Guitar-only intro, custom ending

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

## Rest and stop

```yaml
    chords: "| A7 | A7 | N.C. | E7 |"    # N.C. = the guitar is silent for one bar
```

## Practice session

```sh
# render all the blues at 80 BPM, drums and bass only, as mp3
backingtrack render examples/blues/*.yaml --tempo 80 --mute guitar --bass --mp3 -o practice/
```
