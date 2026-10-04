# Come funziona

![pipeline](../../pipeline.jpg)

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
