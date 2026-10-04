# Come si legge una battuta

Ogni battuta ha **4 tempi**. I simboli scritti nella battuta si dividono i 4 tempi **in parti uguali**,
e il punto `.` **prolunga l'accordo che lo precede** di una parte.

Prendiamo `Em . D C`. Sono 4 simboli, quindi ognuno vale 1 tempo:

| tempo | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| simbolo | `Em` | `.` | `D` | `C` |
| suona | **Em** | Em (continua) | **D** | **C** |

Quindi: **Em per 2 tempi, D per 1, C per 1**. Nell'editor grafico basta passare col mouse sulla battuta: *Em 2 tempi · D 1 · C 1*, e nella striscia del player Em occupa metà casella.

| Scrittura | Significato |
|---|---|
| `\| A7 \|` | A7 per tutta la battuta |
| `\| A7 D7 \|` | due accordi: 2 tempi ciascuno |
| `\| C G Am F \|` | un accordo per tempo |
| `\| Em . D C \|` | Em 2 tempi, D 1, C 1 |
| `\| C . . G \|` | C 3 tempi, G 1 |
| `\| C G F \|` | tre accordi: 1⅓ tempi ciascuno (possibile ma insolito) |
| `\| % \|` | ripete la battuta precedente |
| `\| N.C. \|` | niente chitarra, la batteria continua |

Errori comuni, con il messaggio che ricevi:

| Scrivi | Problema | Correggi |
|---|---|---|
| `. D` | il `.` prolunga l'accordo precedente, quindi non può aprire la battuta | `D` oppure `Em . D C` |
| `am` | la tonica va maiuscola | `Am` |
| `H7` | in notazione inglese il Si è `B` | `B7` |
| `%` come prima battuta | non c'è una battuta precedente da ripetere | scrivi l'accordo |
| `A B C D E` | più di 4 simboli (uno per tempo al massimo) | dividi su due battute |
