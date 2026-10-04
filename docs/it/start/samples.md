# Perché ~460 MB?

Un suono realistico viene da **registrazioni vere**: ogni nota della chitarra e ogni colpo di batteria
sono file audio separati, registrati a più dinamiche (piano, medio, forte) e più volte (i *round robin*,
così due colpi di fila non sono mai identici). Il programma in sé pesa meno di 200 KB: lo spazio è tutto campioni.

`setup` **non scarica le librerie intere**: legge le mappe SFZ e prende **solo i campioni che il programma usa**,
e al massimo 2 round robin per la chitarra e 6 per la batteria. Rispetto alle librerie complete il download scende da ~1,2 GB a ~460 MB.

| Pacchetto | Cosa contiene | `setup` | `setup --full` |
|---|---|---|---|
| `gretsch` 🎸 | Gretsch Anniversary: note normali + staccato, E2–E6 | ~175 MB | ~270 MB |
| `drums` 🥁 | Salamander Drumkit: cassa, rullante, hi-hat, tom, ride, crash | ~120 MB (salvata ~145 MB) | ~185 MB |
| `cabs` 🔈 | 21 impulse response di casse Marshall 4×12 | ~5 MB | ~5 MB |
| `bass` 🎻 | contrabbasso pizzicato (solo con `--bass`) | ~56 MB | ~130 MB |
| `epiphone` 🎸 | chitarra alternativa, Epiphone solid body (opzionale) | ~40 MB | ~100 MB |
| `fender` 🎸 | Fender solid body DI, pickup al ponte: chitarra predefinita | ~160 MB | ~314 MB |
| `acoustic` 🎸 | chitarra acustica steel string Seagull, suonata senza ampli (opzionale, GPL con eccezione) | ~25 MB | ~25 MB |
| `ebass` 🎸 | basso elettrico Black & Blue 'darkblack', a dita (opzionale) | ~80 MB | ~160 MB |
| `sneakybass` 🎻 | contrabbasso Sneakybass, pizzicato leggero (opzionale) | ~63 MB | ~124 MB |

- **Vuoi il massimo?** `backingtrack setup --full` scarica tutti i round robin: più varietà, circa il doppio dello spazio.
- **Vuoi liberare spazio?** `backingtrack remove bass` (o qualsiasi pacchetto); per cancellare tutto elimina la cartella dei campioni.
- **Dove finiscono?** In `~/.local/share/backingtrack` (Linux), `~/Library/Application Support/backingtrack` (macOS)
  o `%LOCALAPPDATA%\backingtrack` (Windows). Puoi cambiare cartella con la variabile `BACKINGTRACK_HOME`
  (es. un disco esterno).
- Si scarica **una volta sola**: poi il programma funziona offline.
