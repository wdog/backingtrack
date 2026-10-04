---
hide:
  - navigation
---

# backingtrack { .sr-only }

![backingtrack](../logo.jpg)

<p align="center">
  <b>Scrivi gli accordi, scegli il groove, suona sopra.</b><br>
  Backing track con chitarra ritmica e batteria <i>campionate da strumenti veri</i>, generate da un semplice file YAML
  o da un editor grafico.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-555">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Styles" src="https://img.shields.io/badge/stili-rock%20%7C%20blues%20%7C%20rockabilly%20%7C%20country%20%7C%20bluegrass%20%7C%20jazz%20%7C%20funk%20%7C%20reggae%20%7C%20soul-F5A623">
  <img alt="Grooves" src="https://img.shields.io/badge/groove-153-8E44AD">
  <img alt="Examples" src="https://img.shields.io/badge/esempi-90%20brani-C0392B">
  <img alt="Languages" src="https://img.shields.io/badge/lingua-Italiano%20%7C%20English-2E86C1">
</p>

![editor: pagina Sezioni](../gui-sezioni-it.jpg)

## ✨ Caratteristiche

- 🎸 **Chitarre vere** (Fender, Gretsch, Epiphone, acustica) con **ampli e casse veri**, **batteria** campionata, **basso** opzionale
- 🎚️ **153 groove** in 9 stili: rock, blues, rockabilly, country, bluegrass, jazz, funk, reggae, soul
- 🖥️ **Editor grafico** con griglia delle battute, modelli di giro, **player** con loop e **scale sulla tastiera** (CAGED)
- 📤 **WAV, MP3, MIDI** e tracce separate; 2 minuti di brano in circa 5 secondi
- 📚 **90 brani di esempio**, interfaccia in italiano e inglese

## 📦 Installazione

```sh
curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash      # Linux / macOS
```

```powershell
irm https://raw.githubusercontent.com/wdog/backingtrack/main/install.ps1 | iex             # Windows
```

Installa ffmpeg se manca, il programma e i campioni (~460 MB, una volta sola). Altro: [installazione](https://wdog.github.io/backingtrack/it/start/install/).

## 🚀 Avvio rapido

```sh
backingtrack examples/blues/sweet_home_chicago.yaml     # → out/sweet_home_chicago.wav
backingtrack gui                                        # editor grafico
```

Un brano sono poche righe di YAML:

```yaml
title: Il mio blues
tempo: 90
groove: blues
sections:
  - name: Strofa
    repeat: 2
    chords: |
      | A7 | D7 | A7 | A7 |
      | D7 | D7 | A7 | A7 |
      | E7 | D7 | A7 | E7 |
```

## 📖 Documentazione

**[wdog.github.io/backingtrack/it](https://wdog.github.io/backingtrack/it/)** — [tutorial](https://wdog.github.io/backingtrack/it/start/tutorial/) ·
[editor](https://wdog.github.io/backingtrack/it/editor/) · [formato](https://wdog.github.io/backingtrack/it/songs/format/) · [groove](https://wdog.github.io/backingtrack/it/grooves/) · [brani](https://wdog.github.io/backingtrack/it/examples/) ·
[comandi](https://wdog.github.io/backingtrack/it/reference/commands/) · [FAQ](https://wdog.github.io/backingtrack/it/reference/faq/) · [sviluppo](https://wdog.github.io/backingtrack/it/dev/)

## 🙏 Crediti

Codice: **MIT**. I campioni li scarica `backingtrack setup` direttamente dai loro autori:

| Libreria | Strumento | Autore | Licenza |
|---|---|---|---|
| [Black & Green Guitars](https://github.com/sfzinstruments/karoryfer.black-and-green-guitars) | chitarra Gretsch | Karoryfer Samples | CC0 1.0 |
| [Emilyguitar](https://github.com/sfzinstruments/karoryfer.emilyguitar) | chitarra Epiphone (opzionale) | Karoryfer Samples / D. Smolken | CC0 1.0 |
| [Electric Guitar FSBS](https://github.com/freepats/electric-guitar-FSBS-direct) | chitarra Fender (default) | FreePats | CC0 1.0 |
| [FSS Steel-String Guitar](https://freepats.zenvoid.org/Guitar/steel-acoustic-guitar.html) | chitarra acustica (opzionale) | FreePats / FlameStudios | GPL 3+ con eccezione per i brani |
| [Jester's Emerald](https://www.jester-dyne-productions.com/emerald-ir-pack/) e [Brutal IR](https://www.jester-dyne-productions.com/brutal-ir-pack/) | casse per chitarra (IR) | Jester Dyne Productions | gratuite, anche per uso commerciale |
| [Salamander Drumkit](https://github.com/studiorack/salamander-drumkit) | batteria | Alexander Holm | CC-BY-SA 3.0 |
| [Double bass (Rubner 1958)](https://github.com/sfzinstruments/dsmolken.double-bass) | contrabbasso (opzionale) | D. Smolken | CC0 1.0 |
| [Sneakybass](https://github.com/sfzinstruments/karoryfer.sneakybass) | contrabbasso leggero (opzionale) | D. Smolken | CC0 1.0 |
| [Black & Blue Basses](https://github.com/sfzinstruments/karoryfer.black-and-blue-basses) | basso elettrico (opzionale) | Karoryfer Samples | CC0 1.0 |

Se pubblichi brani fatti con la batteria Salamander, cita l'autore: *"Drums: Salamander Drumkit by Alexander Holm
(CC-BY-SA 3.0)"*. I brani in `examples/` riportano solo progressioni di accordi; i titoli servono solo a riconoscerle.
