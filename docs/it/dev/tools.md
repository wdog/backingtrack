# Strumenti usati e perché

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
