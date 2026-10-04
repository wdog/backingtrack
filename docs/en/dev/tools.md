# Tools used and why

| Tool | Role | Why this one |
|---|---|---|
| 🐍 **Python 3.8+** | the whole program | everywhere, easy to read and change |
| 🔢 **numpy** | sampling engine, balancing, reverb | sums thousands of notes in a few seconds, nothing to compile |
| 📄 **PyYAML** | reads the song file | YAML is readable and easy to write by hand |
| 🎬 **ffmpeg** | amp, cabinet (`afir` convolution), EQ, compressors, reverb, limiter, MP3, FLAC conversion | professional audio filters in C, very fast, installable on every system |
| 🎹 **SFZ** | instrument format | open standard (text + WAV): free quality libraries with clear licenses |
| 🎸 **Black & Green Guitars** | guitar samples (Gretsch) | sampled on every semitone, with staccato; recorded direct (DI), so the amp is chosen later |
| 🔈 **Jester's IR** | guitar cabinets | impulse responses of miked Marshall 4×12s: the sound of a real cabinet, via convolution |
| 🥁 **Salamander Drumkit** | drum samples | a real acoustic kit, many dynamics and round robins: no "machine-gun effect" |

**Why not a General MIDI soundfont with fluidsynth?** That was the first version: quick to write, but GM guitars
sound fake. Here every instrument is a dedicated multisampled library, and the guitar goes through a simulated amp
as in a studio.

**Why not use an external sampler directly (sfizz, LinuxSampler)?** They are not available evenly on every system.
The built-in numpy engine reads only the subset of SFZ it needs and runs wherever Python runs.
