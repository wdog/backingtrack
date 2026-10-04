# Tutorial: your first backing track

## Step 1 — create the file

```sh
backingtrack new my_song.yaml
```

This creates an example file, already commented. Open it with a text editor.

## Step 2 — tempo and groove

```yaml
title: My blues
tempo: 96          # beats per minute
groove: blues      # see "backingtrack grooves"
```

## Step 3 — write the chords

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

## Step 4 — repeat the sections

```yaml
  - name: Verse
    repeat: 3        # play this section 3 times
```

Or pick the full order with `arrangement` (it overrides `repeat`):

```yaml
arrangement: [Intro, Verse x2, Solo, Verse, Outro]
```

## Step 5 — render and listen

```sh
backingtrack my_song.yaml --mp3
```

## Step 6 — customize

```sh
backingtrack my_song.yaml --tempo 80          # slower, to practice
backingtrack my_song.yaml --transpose 2       # one tone up
backingtrack my_song.yaml --groove blues/slow # try another groove
backingtrack my_song.yaml --bass              # add the double bass
backingtrack my_song.yaml --mute guitar       # drums only (you play the rhythm part)
backingtrack my_song.yaml --stems             # separate tracks
```

Tip: with `--dry-run` you check the structure instantly without rendering audio.
