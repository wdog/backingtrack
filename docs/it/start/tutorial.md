# Tutorial: la tua prima backing track

## Passo 1 — crea il file

```sh
backingtrack new mia_canzone.yaml
```

Si crea un file di esempio già commentato. Aprilo con un editor di testo.

## Passo 2 — tempo e groove

```yaml
title: Il mio blues
tempo: 96          # battiti al minuto
groove: blues      # vedi "backingtrack grooves"
```

## Passo 3 — scrivi gli accordi

Ogni `|` separa una battuta da 4/4. Puoi andare a capo quando vuoi.

```yaml
sections:
  - name: Strofa
    chords: |
      | A7 | D7 | A7 | A7 |
      | D7 | D7 | A7 | A7 |
      | E7 | D7 | A7 | E7 |
```

Due accordi nella stessa battuta si dividono i tempi: `| A7 D7 |` = 2 + 2.
Il punto prolunga l'accordo: `| C . . G |` = 3 + 1.

## Passo 4 — ripeti le sezioni

```yaml
  - name: Strofa
    repeat: 3        # suona 3 volte questa sezione
```

Oppure scegli l'ordine completo con `arrangement` (sovrascrive `repeat`):

```yaml
arrangement: [Intro, Strofa x2, Solo, Strofa, Finale]
```

## Passo 5 — genera e ascolta

```sh
backingtrack mia_canzone.yaml --mp3
```

## Passo 6 — personalizza

```sh
backingtrack mia_canzone.yaml --tempo 80          # più lento per studiare
backingtrack mia_canzone.yaml --transpose 2       # un tono sopra
backingtrack mia_canzone.yaml --groove blues/slow # prova un altro groove
backingtrack mia_canzone.yaml --bass              # aggiungi il contrabbasso
backingtrack mia_canzone.yaml --mute guitar       # solo batteria (suoni tu la ritmica)
backingtrack mia_canzone.yaml --stems             # tracce separate
```

Consiglio: con `--dry-run` controlli la struttura in un istante senza generare audio.
