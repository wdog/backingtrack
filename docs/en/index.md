---
hide:
  - navigation
---

# backingtrack { .sr-only }

![backingtrack](../logo.jpg)

<p align="center">
  <b>Write the chords, pick the groove, play along.</b><br>
  Backing tracks with rhythm guitar and drums <i>sampled from real instruments</i>, generated from a simple YAML file
  or from a graphical editor.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-555">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Styles" src="https://img.shields.io/badge/styles-rock%20%7C%20blues%20%7C%20rockabilly%20%7C%20country%20%7C%20bluegrass%20%7C%20jazz%20%7C%20funk%20%7C%20reggae%20%7C%20soul-F5A623">
  <img alt="Grooves" src="https://img.shields.io/badge/grooves-153-8E44AD">
  <img alt="Examples" src="https://img.shields.io/badge/examples-90%20songs-C0392B">
  <img alt="Languages" src="https://img.shields.io/badge/lang-English%20%7C%20Italiano-2E86C1">
</p>

![editor: Sections page](../gui-sezioni-en.jpg)

## ✨ Features

- 🎸 **Real guitars** (Fender, Gretsch, Epiphone, acoustic) through **real amps and cabinets**, sampled **drums**, optional **bass**
- 🎚️ **153 grooves** in 9 styles: rock, blues, rockabilly, country, bluegrass, jazz, funk, reggae, soul
- 🖥️ **Graphical editor** with bar grid, progression templates, **player** with loop and **scales on the fretboard** (CAGED)
- 📤 **WAV, MP3, MIDI** and stems; 2 minutes of song in about 5 seconds
- 📚 **90 example songs**, English and Italian interface

## 📦 Install

```sh
curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash      # Linux / macOS
```

```powershell
irm https://raw.githubusercontent.com/wdog/backingtrack/main/install.ps1 | iex             # Windows
```

It installs ffmpeg if missing, the program and the samples (~460 MB, only once). More: [installation](https://wdog.github.io/backingtrack/start/install/).

## 🚀 Quick start

```sh
backingtrack examples/blues/sweet_home_chicago.yaml     # → out/sweet_home_chicago.wav
backingtrack gui                                        # graphical editor
```

A song is a few lines of YAML:

```yaml
title: My blues
tempo: 90
groove: blues
sections:
  - name: Verse
    repeat: 2
    chords: |
      | A7 | D7 | A7 | A7 |
      | D7 | D7 | A7 | A7 |
      | E7 | D7 | A7 | E7 |
```

## 📖 Documentation

**[wdog.github.io/backingtrack](https://wdog.github.io/backingtrack/)** — [tutorial](https://wdog.github.io/backingtrack/start/tutorial/) ·
[editor](https://wdog.github.io/backingtrack/editor/) · [song format](https://wdog.github.io/backingtrack/songs/format/) · [grooves](https://wdog.github.io/backingtrack/grooves/) · [songs](https://wdog.github.io/backingtrack/examples/) ·
[commands](https://wdog.github.io/backingtrack/reference/commands/) · [FAQ](https://wdog.github.io/backingtrack/reference/faq/) · [development](https://wdog.github.io/backingtrack/dev/)

## 🙏 Credits

Code: **MIT**. The samples are downloaded by `backingtrack setup` straight from their authors:

| Library | Instrument | Author | License |
|---|---|---|---|
| [Black & Green Guitars](https://github.com/sfzinstruments/karoryfer.black-and-green-guitars) | Gretsch guitar | Karoryfer Samples | CC0 1.0 |
| [Emilyguitar](https://github.com/sfzinstruments/karoryfer.emilyguitar) | Epiphone guitar (optional) | Karoryfer Samples / D. Smolken | CC0 1.0 |
| [Electric Guitar FSBS](https://github.com/freepats/electric-guitar-FSBS-direct) | Fender guitar (default) | FreePats | CC0 1.0 |
| [FSS Steel-String Guitar](https://freepats.zenvoid.org/Guitar/steel-acoustic-guitar.html) | acoustic guitar (optional) | FreePats / FlameStudios | GPL 3+ with an exception for songs |
| [Jester's Emerald](https://www.jester-dyne-productions.com/emerald-ir-pack/) and [Brutal IR](https://www.jester-dyne-productions.com/brutal-ir-pack/) | guitar cabinets (IR) | Jester Dyne Productions | free, commercial use allowed |
| [Salamander Drumkit](https://github.com/studiorack/salamander-drumkit) | drums | Alexander Holm | CC-BY-SA 3.0 |
| [Double bass (Rubner 1958)](https://github.com/sfzinstruments/dsmolken.double-bass) | double bass (optional) | D. Smolken | CC0 1.0 |
| [Sneakybass](https://github.com/sfzinstruments/karoryfer.sneakybass) | light double bass (optional) | D. Smolken | CC0 1.0 |
| [Black & Blue Basses](https://github.com/sfzinstruments/karoryfer.black-and-blue-basses) | electric bass (optional) | Karoryfer Samples | CC0 1.0 |

If you publish songs made with the Salamander drums, credit the author: *"Drums: Salamander Drumkit by Alexander Holm
(CC-BY-SA 3.0)"*. The songs in `examples/` contain only chord progressions; the titles are there only to recognize them.
