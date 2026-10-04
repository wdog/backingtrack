# ⚙️ Come funziona e struttura del progetto

<!-- nav -->
<p align="center">
  <a href="../../README.it.md">🏠 Home</a> ·
  <a href="installazione.md">📦 Installazione</a> ·
  <a href="gui.md">🖥️ Editor grafico</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="formato.md">📝 Formato</a> ·
  <a href="groove.md">🥁 Groove</a> ·
  <a href="brani.md">📚 Brani</a> ·
  <a href="comandi.md">⌨️ Comandi</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <b>⚙️ Sviluppo</b>
</p>
<p align="center"><b>🇮🇹 Italiano</b> · <a href="../en/development.md">🇬🇧 English</a></p>
<!-- /nav -->

## ⚙️ Come funziona

<p align="center"><img src="../pipeline.jpg" alt="pipeline" width="900"></p>

1. **`song.yaml`** — descrivi tempo, groove e sezioni con gli accordi, battuta per battuta.
2. **Arranger** — trasforma ogni accordo in un *voicing* sulle 6 corde e applica il pattern del groove:
   pennate (con lo sfasamento reale tra una corda e l'altra), swing, accenti, fill, variazioni, umanizzazione.
   Il risultato è una lista di note, come in un MIDI.
3. **Sampler** — per ogni nota sceglie il campione giusto (tasto, dinamica, round robin), lo intona
   e lo mette nel punto esatto della traccia. Lo fa un piccolo motore scritto in **numpy** che legge
   il formato **SFZ**, lo standard aperto per gli strumenti campionati.
4. **Mixer** — **ffmpeg** fa passare la chitarra "diretta" (DI) in una catena ampli + cassa, comprime ed equalizza
   la batteria, aggiunge slapback e riverbero, bilancia i volumi e porta tutto a un livello d'ascolto costante.
5. **Output** — WAV/MP3 da ascoltare, MIDI da aprire in una DAW, stems per mixare a piacere.

### 🧰 Strumenti usati e perché

| Strumento | Ruolo | Perché questo |
|---|---|---|
| 🐍 **Python 3.8+** | tutto il programma | ovunque, facile da leggere e modificare |
| 🔢 **numpy** | motore di campionamento, bilanciamento, riverbero | somma migliaia di note in pochi secondi, senza compilare niente |
| 📄 **PyYAML** | legge il file canzone | YAML è leggibile e si scrive a mano senza fatica |
| 🎬 **ffmpeg** | ampli, cassa (convoluzione `afir`), EQ, compressori, riverbero, limiter, MP3, conversione FLAC | filtri audio professionali in C, velocissimi, installabile su ogni sistema |
| 🎹 **SFZ** | formato degli strumenti | standard aperto (testo + WAV): librerie di qualità gratuite e con licenze chiare |
| 🎸 **Black & Green Guitars** | campioni di chitarra (Gretsch) | campionata ogni semitono, con staccato; registrata in diretta (DI), quindi l'ampli si sceglie dopo |
| 🔈 **Jester's IR** | casse per chitarra | impulse response di Marshall 4×12 microfonate: il suono di una cassa vera, via convoluzione |
| 🥁 **Salamander Drumkit** | campioni di batteria | kit acustico vero, tante dinamiche e round robin: niente "effetto mitraglietta" |

**Perché non un soundfont General MIDI con fluidsynth?** È stata la prima versione: veloce da scrivere, ma
le chitarre GM suonano finte. Qui ogni strumento è una libreria multicampionata dedicata, e la chitarra
passa da un ampli simulato come si fa in studio.

**Perché non usare direttamente un sampler esterno (sfizz, LinuxSampler)?** Non sono disponibili in modo
uniforme su tutti i sistemi. Il motore interno in numpy legge solo il sottoinsieme di SFZ che serve ed
è portabile ovunque giri Python.

## 🌐 Traduzioni

I testi sono scritti in italiano nel codice e avvolti in `_()` (`backingtrack/i18n.py`); le traduzioni inglesi stanno in
`backingtrack/locale_en.py` (`EN` per i testi, `GROOVES_EN` per le descrizioni dei groove). Le costanti di modulo (la
guida F1, le descrizioni delle scale…) restano grezze e si traducono dove vengono mostrate. Un test fallisce se un testo
non ha la traduzione o se i segnaposto `%s` non coincidono. La documentazione sta in `docs/it/` e `docs/en/`;
`python3 docs/make_docs.py` rigenera dai dati le tabelle di groove e brani e la barra di navigazione di ogni pagina.

## 🗂️ Struttura del progetto

```
backingtrack/
├── backingtrack/
│   ├── cli.py         # comandi
│   ├── gui.py         # editor grafico GTK 4 / libadwaita
│   ├── songfile.py    # modello dell'editor: validazione, modelli di giro, YAML
│   ├── i18n.py        # lingua: _(), inglese predefinito, preferenza dell'editor
│   ├── locale_en.py   # traduzioni inglesi
│   ├── data/          # icona dell'app
│   ├── song.py        # lettura YAML, battute, arrangement
│   ├── theory.py      # accordi, voicing sulle corde, scale, CAGED, scale suggerite
│   ├── grooves.py     # pattern di chitarra e batteria
│   ├── arranger.py    # accordi → note (pennate, swing, fill, umanizzazione)
│   ├── sfz.py         # lettore SFZ e WAV
│   ├── render.py      # sampler numpy
│   ├── mixer.py       # ampli, EQ, riverbero, loudness (ffmpeg)
│   ├── packs.py       # download selettivo dei campioni
│   └── midi.py        # export MIDI
├── examples/          # brani di esempio (blues, rock, rockabilly, country, bluegrass, jazz)
├── docs/              # documentazione it/ ed en/, immagini, make_docs.py, make_images.py
├── tests/             # python -m unittest discover tests
├── install.sh         # installer Linux/macOS
├── install.ps1        # installer Windows
└── pyproject.toml
```

<!-- foot -->
---

<p align="center"><a href="faq.md">⬅ Precedente: ❓ FAQ</a> · <a href="#">⬆ Inizio pagina</a></p>
<!-- /foot -->
