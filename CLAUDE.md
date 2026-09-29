# CLAUDE.md

Guida per Claude Code su questo repository.

## Progetto

`backingtrack`: CLI Python che genera backing track (chitarra ritmica + batteria, contrabbasso opzionale)
da un file YAML con tempo, groove, sezioni ripetibili e accordi. Stili: rock, blues, rockabilly.
Lingua di UI, messaggi di errore, commenti e documentazione: **italiano**.

## Comandi

```sh
python3 -m backingtrack setup [--bass]            # scarica campioni SFZ (una volta)
python3 -m backingtrack examples/blues/sweet_home_chicago.yaml [--mp3 --stems --bass]
python3 -m backingtrack render examples/*/*.yaml --dry-run   # valida tutti gli esempi
python3 -m backingtrack doctor                    # dipendenze e campioni installati
python3 -m unittest discover tests                # test (non servono i campioni)
backingtrack gui [file.yaml]                      # editor GTK4 / libadwaita
backingtrack update [--src DIR]                   # campioni mancanti + aggiornamento programma
python3 docs/make_images.py                       # rigenera logo/diagramma (Pillow, font DejaVu)
shellcheck install.sh                             # installer curl|bash (Linux/macOS)
```

Output sempre in `out/<nome>.{wav,mp3,mid}` (ignorato da git). Mai scrivere output dentro `examples/`.

## Architettura (`backingtrack/`)

Pipeline: `song.py` → `arranger.py` → `render.py` (+ `sfz.py`) → `mixer.py`; `cli.py` orchestra.

- `theory.py` — `Chord`: parsing simboli (tabella `QUALITIES`), voicing barré forma MI/LA.
  Ogni voicing ritorna `[(pitch, corda)]` con corda 6 = MI grave.
- `grooves.py` — `GROOVES`: pattern chitarra/batteria per battuta 4/4 (beat float, `.5` = levare swingato),
  più `amp`, `double`, `slap`, `swing`, `turn` (variazione ogni 4 battute), `fill` (fine sezione).
- `song.py` — YAML → timeline di battute. `| A . D . | % | N.C. |`; `arrangement` con `Nome xN`.
- `arranger.py` — timeline → `Note(part, start, end, pitch, vel, string, muted, bus)` in tick (PPQ 480).
  `part`: guitar/guitar2/bass/drums. `bus` chitarra = `gtr:<amp>:<L|R|C>[:slap]`.
  `_choke`: una nota per corda, basso monofonico. Batteria in numeri GM.
- `midi.py` — export MIDI type 1 per DAW (non usato per l'audio).
- `songfile.py` — modello dell'editor, senza GTK: `SONG_DEFAULTS`, `from_song_dict`/`to_song_dict`/`to_yaml`
  (solo valori non di default, `chords` come blocco `|`), `check_bar`/`describe_bar` (messaggi e lettura
  "Em 2 tempi · D 1 · C 1"), `TEMPLATES` a gradi (I, IV, V:7, vi:m…) → `template_bars(nome, tonalità)`.
- `gui.py` — Adw.Application: schede Brano / Sezioni (3 colonne: elenco | accordi | impostazioni+modelli;
  `Adw.OverlaySplitView` con `pin_sidebar`, si chiude solo < 600sp; colonne impilate < 820sp) / Arrangiamento / YAML;
  barra menu File, Sezione, Brano, Riproduzione, Aiuto. Render in un thread con `cli.render(song_dict, out)`.
  Widget: `MenuRow` (pulsante-menu con sottomenu: `GrooveRow`, `ChoiceRow`, modelli), `GridPicker`/`PickerRow`
  (griglie note/tipi), `BarCell` (griglia battute; drag & drop con payload stringa 'chord:X' / 'bar:N', tasto destro),
  tavolozza accordi. Tutti espongono `selected` + get/set_selected come Adw.ComboRow (niente Gtk.DropDown/ComboRow).
  Player: `Player` (Gtk.MediaFile, forma d'onda PNG da ffmpeg `showwavespic`, linee sezioni) + `ChordStrip`
  (ScrolledWindow orizzontale, battute larghe quanto il testo, autoscroll salvo scroll manuale), dati da `song_bars()`.
  Scorciatoie Spazio/B/S via `EventControllerKey` in CAPTURE, ignorate se il focus è un `Gtk.Editable`.
  Bozza automatica in `data_dir()/bozza.json`, proposta al riavvio. Colori sezione `SECTION_COLORS`, accento #e8811a.
- `sfz.py` — parser SFZ minimale + `read_wav` (RIFF proprio: PCM 8/16/24/32 e float) + `Instrument.select`.
- `render.py` — `Sampler`: region → campione trasposto (np.interp, cache) → voci; choke `group/off_by`;
  `mix_voices` somma nei bus stereo float32 con release, palm mute (decadimento + FIR passa-basso).
- `mixer.py` — ffmpeg: catena per bus in parallelo (ampli `AMPS`, EQ, comp, slapback), numpy bilancia le
  famiglie (`LEVELS`) e prepara la mandata; ffmpeg fa riverbero a convoluzione (`afir` con IR generata),
  glue compressor, gain di loudness e `alimiter`.
- `packs.py` — pacchetti campioni (`PACKS`). Repo GitHub: download **selettivo** file per file da
  raw.githubusercontent (API tree → SFZ → `_needed_samples` → solo campioni usati, max `rr` round robin;
  `setup --full` = senza limite). MAI usare gli zip di GitHub: applicano `.gitattributes` (`eol=crlf`) e
  corrompono i WAV (successo con black-and-green-guitars). IR casse (`cabs`) da zip Jester (ok). FLAC→WAV 16 bit.
  Dati in `~/.local/share/backingtrack` (Linux), `~/Library/Application Support/...` (macOS),
  `%LOCALAPPDATA%\backingtrack` (Windows); override con `BACKINGTRACK_HOME`. Mappa GM→Salamander in `SALAMANDER_MAP`.

## Installazione e distribuzione

- Repo GitHub: `wdog/backingtrack`, branch `main`. Pacchetto via `pyproject.toml` (entry point `backingtrack.cli:main`).
- `install.sh` (`curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash`):
  controlla Python ≥3.8, installa ffmpeg (chiede via `/dev/tty`), usa pipx o un venv in `~/.local/share/backingtrack/venv`,
  poi `backingtrack setup`. Variabili: `BT_BASS`, `BT_NO_SAMPLES`, `BT_YES`, `BT_REF`, `BT_SRC` (sorgente locale per test:
  `HOME=/tmp/h BT_SRC=$PWD BT_NO_SAMPLES=1 bash install.sh`).
- `install.ps1`: equivalente Windows (`irm ... | iex`), venv in `%LOCALAPPDATA%\backingtrack`.
- README: indice in cima; le tabelle groove ed elenco brani vanno tenute allineate a `GROOVES` e `examples/`.

## Campioni

- chitarra (default `gretsch`): Karoryfer Black & Green Guitars, Gretsch "green" (CC0), DI, ogni semitono;
  `Programs/04-green_twang.sfz` + `05-green_staccato.sfz` per le note stoppate (`muted="real"`).
  Alternativa `epiphone` = Emilyguitar (CC0), palm mute simulato. Scelta con `guitar:` nel YAML.
- casse: Jester's Emerald (Marshall 4x12 Greenback) + Brutal (V30), IR 44.1 kHz; `AMPS[amp]["ir"]`, convoluzione
  `afir` in `mixer.bus_graph`; senza IR si usa `cab_eq`.
- batteria: Salamander Drumkit (CC-BY-SA 3.0), hi-hat aperto/chiuso via CC4 sul tasto 42.
- basso: D. Smolken double bass pizz (CC0), opzionale.
Nessun campione nel repo: si scaricano con `setup` (~300 MB default). `sfz.Instrument.select` ripiega su un round robin
presente se quello estratto non è installato. `backingtrack remove <pack>` libera spazio.

## GUI: note

- PyGObject viene dal sistema: pipx/venv vanno creati con `--system-site-packages` (installer, `update` e README lo fanno).
- Test manuali headless-ish: app di prova che cattura la finestra con `Gtk.WidgetPaintable` + `render_texture`
  (le immagini del README in `docs/gui-*.jpg` sono fatte così, finestra forzata 1280×820 con `set_size_request`).
- `Gtk.MediaFile` ha `is_prepared()`, non `get_prepared()`; il seek prima di `is_prepared()` viene ignorato.
- Nei test automatici la finestra non riceve frame: le animazioni (Revealer, OverlaySplitView) restano a metà.
  Il player usa Revealer senza transizione; per le schermate impostare `gtk-enable-animations` a False.
- Adw.ToggleGroup non ha stile con questo tema e all'utente non piaceva: usare menu (`ChoiceRow`).

## Vincoli e scelte

- Dipendenze: solo Python ≥3.8, numpy, PyYAML, ffmpeg nel PATH. Niente fluidsynth/soundfont GM
  (scartati: suono poco realistico). Niente scipy.
- Performance: render di un brano di 2 min ~4-7 s. Evitare `loudnorm` a 2 passaggi e l'oversampling
  4× in ffmpeg (lentissimi). Il rumore a -140 dB prima delle catene evita i denormali nei filtri IIR.
- Solo 4/4. Il 12/8 si ottiene con beat in terzine (`T1`, `T2`) e swing.
- Esempi in `examples/<stile>/`: solo progressioni di accordi di brani celebri (niente melodia/testi).

## Aggiungere un groove

Nuova voce in `GROOVES` con `desc, amp, double, swing, bass_style, guitar, drums, turn, fill`.
Tipi evento chitarra: `D U C P B B5 R5 R6 R7` + suffisso `m` (stoppato). Aggiornare la tabella groove nel README.

## Aggiungere un ampli

Nuova chiave in `mixer.AMPS` (catena ffmpeg su segnale mono DI a -20 dBFS RMS) e usarla come `amp` di un groove.
