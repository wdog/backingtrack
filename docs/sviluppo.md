# ⚙️ Come funziona e struttura del progetto

[⬅ README](../README.md) · [Installazione](installazione.md) · [Editor grafico](gui.md) · [Tutorial ed esempi](tutorial.md) · [Formato](formato.md) · [Groove](groove.md) · [Brani](brani.md) · [Comandi](comandi.md) · [FAQ](faq.md) · [Sviluppo](sviluppo.md)

## ⚙️ Come funziona

<p align="center"><img src="pipeline.jpg" alt="pipeline" width="900"></p>

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

## 🗂️ Struttura del progetto

```
backingtrack/
├── backingtrack/
│   ├── cli.py         # comandi
│   ├── gui.py         # editor grafico GTK 4 / libadwaita
│   ├── songfile.py    # modello dell'editor: validazione, modelli di giro, YAML
│   ├── data/          # icona dell'app
│   ├── song.py        # lettura YAML, battute, arrangement
│   ├── theory.py      # accordi e voicing sulle corde
│   ├── grooves.py     # pattern di chitarra e batteria
│   ├── arranger.py    # accordi → note (pennate, swing, fill, umanizzazione)
│   ├── sfz.py         # lettore SFZ e WAV
│   ├── render.py      # sampler numpy
│   ├── mixer.py       # ampli, EQ, riverbero, loudness (ffmpeg)
│   ├── packs.py       # download selettivo dei campioni
│   └── midi.py        # export MIDI
├── examples/          # brani di esempio (blues, rock, rockabilly)
├── docs/              # documentazione (una pagina per argomento) e immagini
├── tests/             # python -m unittest discover tests
├── install.sh         # installer Linux/macOS
├── install.ps1        # installer Windows
└── pyproject.toml
```
