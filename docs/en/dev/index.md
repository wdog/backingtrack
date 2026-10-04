# How it works

![pipeline](../../pipeline.jpg)

1. **`song.yaml`** — describe tempo, groove and sections with their chords, bar by bar.
2. **Arranger** — turns each chord into a *voicing* on the 6 strings and applies the groove pattern:
   strums (with the real delay between one string and the next), swing, accents, fills, variations, humanization.
   The result is a list of notes, as in a MIDI file.
3. **Sampler** — for each note it picks the right sample (key, dynamics, round robin), tunes it
   and places it at the exact point of the track. A small engine written in **numpy** does it, reading
   the **SFZ** format, the open standard for sampled instruments.
4. **Mixer** — **ffmpeg** runs the "direct" (DI) guitar through an amp + cabinet chain, compresses and equalizes
   the drums, adds slapback and reverb, balances the levels and brings everything to a steady listening loudness.
5. **Output** — WAV/MP3 to listen to, MIDI to open in a DAW, stems to mix as you like.
