# CLAUDE.md

Guida per Claude Code su questo repository.

## Progetto

`backingtrack`: CLI Python che genera backing track (chitarra ritmica + batteria, contrabbasso opzionale)
da un file YAML con tempo, groove, sezioni ripetibili e accordi. Stili: rock, blues, rockabilly, country, jazz, funk, reggae, soul (≥15 groove ciascuno).
Codice e commenti in **italiano**; UI, messaggi e documentazione in **italiano e inglese**: testi scritti in italiano
avvolti in `_()` (`i18n.py`), traduzioni in `locale_en.py` (`EN`, `GROOVES_EN`); un test fallisce se ne manca una.
Le costanti di modulo (HELP, SCALE_DESC…) restano grezze e si traducono dove vengono mostrate (mai `_()` a livello di
modulo o nei default degli argomenti). Lingua GUI: Aiuto › Lingua (gui.json `lang`, riavvio con la bozza);
CLI: `BACKINGTRACK_LANG` o lingua di sistema.

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
- `gui.py` — Adw.Application: schede Brano (+ ordine sezioni) / Sezioni (3 colonne: elenco | Accordi/Scale (`center_stack`) | impostazioni+modelli;
  `Adw.OverlaySplitView` con `pin_sidebar`, si chiude solo < 600sp; colonne impilate < 820sp) / YAML.
  Solo le impostazioni base in vista: il resto passa da `self.advanced(widget)` ed è mostrato dall'azione stateful
  `app.advanced` (pulsanti "Avanzate", ricordata in `data_dir()/gui.json`). Spiegazioni nei tooltip, non nei sottotitoli.
  Genera e ascolta: `Alt+G` (anche `Ctrl+R`).
  barra menu File, Sezione, Brano, Riproduzione, Aiuto. Render in un thread con `cli.render(song_dict, out)`.
  Widget: `MenuRow` (pulsante-menu con sottomenu: `GrooveRow`, `ChoiceRow`, modelli), `GridPicker`/`PickerRow`
  (griglie note/tipi), `BarCell` (griglia battute; drag & drop con payload stringa 'chord:X' / 'bar:N', tasto destro),
  tavolozza accordi (niente costruttore: gli accordi si scrivono a mano o dalla tavolozza), `Fretboard` (DrawingArea:
  scala + box CAGED da `theory.SCALES`/`caged_boxes`/`fretboard_notes`; più box adiacenti = stringa in ordine CAGED
  ciclico gestita da `theory.toggle_box`, chip + clic sulle fasce). Nomi note per lettera di grado (`scale_names`).
  Pannelli richiudibili: ← in cima all'elenco / «Sezioni →» nella riga dei tab / F9 (`split.show-sidebar`);
  colonna destra uguale e speculare: → in `right_panel` / «← Impostazioni» / Shift+F9 (`right_panel.visible`). Opzioni scale su una riga: dei MenuRow
  si usa solo `.button` (il gruppo d'azioni `row.` è inserito anche sul pulsante). Tutti espongono `selected` + get/set_selected come Adw.ComboRow (niente Gtk.DropDown/ComboRow).
  Player: `Player` (Gtk.MediaFile, forma d'onda PNG da ffmpeg `showwavespic`, linee sezioni) + `ChordStrip`
  (ScrolledWindow orizzontale, battute larghe quanto il testo, numero battuta in piccolo, autoscroll salvo scroll manuale),
  dati da `song_bars()` (`num` = battuta 1…, None per conteggio/finale; `local`/`size` = battuta nella sezione, a destra
  nella striscia); sotto il tempo "Battuta N / tot · sezione L / size". Guida `HELP` (F1, Aiuto › Guida; il popover ? degli
  accordi riusa `BAR_EXAMPLES`/`CHORD_EXAMPLES`): tenerla allineata ai controlli.
  Loop X–Y: `Player.loop_btn/loop_from/loop_to`, `loop_range()` in secondi, `_tick` riporta all'inizio;
  Shift+clic sulla striscia = `set_loop`. Guida: `HELP` = pagine di voci renderizzate da `help_page()`.
  Scorciatoie Spazio/B/S/L via `EventControllerKey` in CAPTURE, ignorate se il focus è un `Gtk.Editable`.
  Bozza automatica in `data_dir()/bozza.json`, proposta al riavvio. Colori sezione `SECTION_COLORS`, tema Dracula (sfondi `@define-color`, accento viola #bd93f9, rosa #ff79c6, forzato scuro).
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
  su Linux scrive `~/.local/share/applications/io.github.wdog.backingtrack.desktop` + icona hicolor (dal pacchetto),
  poi `backingtrack setup`. Variabili: `BT_BASS`, `BT_NO_SAMPLES`, `BT_YES`, `BT_REF`, `BT_SRC` (sorgente locale per test:
  `HOME=/tmp/h BT_SRC=$PWD BT_NO_SAMPLES=1 bash install.sh`).
- `install.ps1`: equivalente Windows (`irm ... | iex`), venv in `%LOCALAPPDATA%\backingtrack`.
- Documentazione: `README.md` (inglese) e `README.it.md` (italiano), corti; il resto in `docs/en/` e `docs/it/`
  (una pagina per argomento, stessi contenuti). `python3 docs/make_docs.py` genera le tabelle di groove e brani dai dati
  e la barra di navigazione (bandiere, avanti/indietro) di ogni pagina: rilanciarlo dopo ogni modifica. Screenshot
  `docs/gui-{brano,sezioni,scale,guida}-{it,en}.jpg`.
- chitarra (default `gretsch`): Karoryfer Black & Green Guitars, Gretsch "green" (CC0), DI, ogni semitono;
  `Programs/04-green_twang.sfz` + `05-green_staccato.sfz` per le note stoppate (`muted="real"`).
  Alternativa `epiphone` = Emilyguitar (CC0), palm mute simulato. Scelta con `guitar:` nel YAML.
  `fender` = FreePats FSBS direct (Fender DI ponte, CC0, repo GitHub), per rock/hard rock.
  `acoustic` = FreePats FSS Seagull steel string (GPL+eccezione, tar.xz da freepats.zenvoid.org): `amp="acoustic"` nel
  pacchetto → `cli.render` sostituisce l'ampli dei bus chitarra con `AMPS["acoustic"]` (senza IR né cassa).
  Scartati: Shinyguitar archtop (brutta), Martin HD28 del Discord GM (15 campioni), BJAM/Ella G. (RAR su Google Drive).
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
  Il player usa Revealer SLIDE_UP con durata 0 (con NONE/CROSSFADE il Revealer nascosto occupa tutta l'altezza
  del figlio e copre la pagina); per le schermate impostare `gtk-enable-animations` a False.
- Esempi nel menu: `pyproject` installa `examples/` come `backingtrack/examples` (package-dir); `EXAMPLES` cerca
  prima nel pacchetto, poi nel repo.
- Il CSS ha uno stile proprio per pulsanti, menu (`.picker`), spinbutton, liste e switch (selettori `window …`),
  perché il tema di sistema li rende squadrati. `.danger` = pulsante distruttivo morbido.
- Adw.ToggleGroup non ha stile con questo tema e all'utente non piaceva: usare menu (`ChoiceRow`).
- Il CSS dell'app è registrato a `STYLE_PROVIDER_PRIORITY_USER + 1`: il `~/.config/gtk-4.0/gtk.css` dell'utente
  (tema tipo Arc) altrimenti ridipinge di blu `suggested-action`, slider e bordi. Selettori specifici (`.player button.play-btn`).

## Vincoli e scelte

- Dipendenze: solo Python ≥3.8, numpy, PyYAML, ffmpeg nel PATH. Niente fluidsynth/soundfont GM
  (scartati: suono poco realistico). Niente scipy.
- Performance: render di un brano di 2 min ~4-7 s. Evitare `loudnorm` a 2 passaggi e l'oversampling
  4× in ffmpeg (lentissimi). Il rumore a -140 dB prima delle catene evita i denormali nei filtri IIR.
- Solo 4/4. Il 12/8 si ottiene con beat in terzine (`T1`, `T2`) e swing.
- Esempi in `examples/<stile>/`: solo progressioni di accordi di brani celebri (niente melodia/testi).

## Aggiungere un groove

Nuova voce in `GROOVES` con `desc, amp, double, swing, bass_style, guitar, drums, turn, fill`; i groove aggiunti usano
`g(desc, amp, guitar, drums, turn, fill, bass=, swing=, ...)` e `pat("D.DU.UDU")` (8/12/16 caratteri = ottavi/terzine/
sedicesimi; maiuscolo forte, minuscolo piano; D U X=chop M/N=stoppati P/p J B F=quinta, `.` pausa, `-` tiene).
Bassi (`arranger.bass_bar`): eighths rootfifth stop slow walk two octave funk reggae quarters dotted tumbao.
Nuovo stile = prefisso del nome + `STYLE_EMOJI`/`STYLE_NAMES` in gui.py + logo (`docs/make_images.py`).
Batteria: solo note in `SALAMANDER_MAP` (niente cowbell/clap: si usa `BELL` 53 = campana del ride).
Tipi evento chitarra: `D U C P B B5 R5 R6 R7 J` (J = voicing jazz a 4 note, `Chord.jazz`).
  Voicing di D/U/C: `Chord.voicing(barre|open|jazz|triad)`, default del groove (`voicing=`), il brano lo cambia con
  `voicing:`; forme aperte in `theory.OPEN_SHAPES` (open ripiega sul barré) + suffisso `m` (stoppato). Aggiornare la tabella in `docs/groove.md`.

## Aggiungere un ampli

Nuova chiave in `mixer.AMPS` (catena ffmpeg su segnale mono DI a -20 dBFS RMS) e usarla come `amp` di un groove.

## Stato e prossimi passi (29/09/2026)

Stato: `main` = `gui` (commit f8d0d2c), tutto committato, nessun remote (da pubblicare su github.com/wdog/backingtrack).
Installazione locale: pipx editable con `--system-site-packages` (il comando `backingtrack` usa i file del repo).

Da fare / verificare:
1. Drag & drop reale col mouse nella griglia battute e dalla tavolozza (verificata solo la logica simulata).
2. Celle battute: 4 per riga anche con colonna accordi stretta (entry width_chars=3, da verificare a vista).
3. Ascoltare i groove nuovi (rock/halftime, gallop, pop, blues/rhumba, funk, stop, country, country/shuffle).
4. Pubblicare: `git remote add origin …`, push `main` e `gui`; poi provare `curl … install.sh | bash` e `backingtrack update`.
5. Idee non fatte: batteria multi-microfono (Naked Drums, 1,3 GB) come pacchetto opzionale; IR di cassa aperta tipo Fender per clean/rockabilly.

Preferenze dell'utente sulla GUI: niente tendine strette (Adw.ComboRow/Gtk.DropDown) né pulsanti segmentati;
sì a pulsanti-menu con sottomenu e griglie; battute compatte a griglia col colore sezione; gli piace la barra del player.
Aggiornare sempre README/docs (e CLAUDE.md) quando cambia qualcosa di visibile.
