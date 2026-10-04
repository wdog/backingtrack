# Esempi

## 12-bar blues con intro e solo

```yaml
title: 12-bar blues in A
tempo: 100
groove: blues

sections:
  - name: Intro
    chords: "| E7 | D7 | A7 | E7 |"      # turnaround
  - name: Strofa
    repeat: 3
    chords: |
      | A7 | D7 | A7 | A7 |
      | D7 | D7 | A7 | A7 |
      | E7 | D7 | A7 | E7 |
  - name: Solo
    groove: blues/7                       # boogie con la settima
    repeat: 2
    chords: |
      | A7 | D7 | A7 | % |
      | D7 | %  | A7 | % |
      | E7 | D7 | A7 D7 | A7 E7 |
```

## Canzone rock: strofa palm mute, ritornello aperto

```yaml
title: Rock in E
tempo: 132
groove: rock                    # power chord con palm mute, chitarre doppiate

sections:
  - name: Strofa
    chords: |
      | E5 | E5 | D5 A5 | E5 |
      | E5 | E5 | D5 A5 | B5 |
  - name: Ritornello
    groove: rock/strum          # accordi aperti in crunch
    chords: "| A | E | B | E |"
  - name: Bridge
    groove: rock/drive
    volume: 0.9                 # un po' più piano
    chords: "| C#m | A | E | B |"

arrangement: [Strofa x2, Ritornello x2, Strofa, Ritornello x2, Bridge x2, Ritornello x2]
```

## Rockabilly con contrabbasso e slapback

```yaml
title: Rockabilly in E
tempo: 172
groove: rockabilly      # boom-chick + train beat
bass: true

sections:
  - name: Strofa
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

## Intro solo chitarra, finale personalizzato

```yaml
title: Ballad
tempo: 70
groove: rock/ballad
ending_chord: Gadd9     # accordo finale (default: il primo del brano)
count_in: false

sections:
  - name: Intro
    drums: false        # la batteria entra dopo
    chords: "| G | D/F# | Em | C |"
  - name: Strofa
    repeat: 2
    chords: "| G | D/F# | Em | C | G | D | C | C |"
```

## Pausa e stop

```yaml
    chords: "| A7 | A7 | N.C. | E7 |"    # N.C. = la chitarra tace per una battuta
```

## Sessione di studio

```sh
# genera tutti i blues a 80 BPM, solo batteria e basso, in mp3
backingtrack render examples/blues/*.yaml --tempo 80 --mute guitar --bass --mp3 -o studio/
```
