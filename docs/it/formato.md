# 📝 Formato della canzone

<!-- nav -->
<p align="center">
  <a href="../../README.it.md">🏠 Home</a> ·
  <a href="installazione.md">📦 Installazione</a> ·
  <a href="gui.md">🖥️ Editor grafico</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <b>📝 Formato</b> ·
  <a href="groove.md">🥁 Groove</a> ·
  <a href="brani.md">📚 Brani</a> ·
  <a href="comandi.md">⌨️ Comandi</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="sviluppo.md">⚙️ Sviluppo</a>
</p>
<p align="center"><b>🇮🇹 Italiano</b> · <a href="../en/format.md">🇬🇧 English</a></p>
<!-- /nav -->

### Chiavi principali

| Chiave | Default | Descrizione |
|---|---|---|
| `title` | nome file | titolo |
| `tempo` | `120` | BPM (30-320) |
| `groove` | `rock` | groove di default ([elenco](groove.md)) |
| `sections` | — | elenco delle sezioni (obbligatorio) |
| `arrangement` | ordine delle sezioni | es. `[Intro, Strofa x2, Rit]` |
| `transpose` | `0` | semitoni (+/-) |
| `swing` | dal groove | 0 = dritto … 1 = terzinato |
| `count_in` | `true` | una battuta di bacchette prima di partire |
| `ending` | `true` | accordo finale con piatto |
| `ending_chord` | primo accordo | accordo del finale |
| `fills` | `true` | rullata sull'ultima battuta di ogni sezione |
| `crash` | `true` | piatto all'inizio di ogni sezione |
| `bass` | `false` | `true` = contrabbasso, oppure `ebass` (elettrico) o `sneakybass` (serve `setup <nome>`) |
| `voicing` | dal groove | forma degli accordi pieni: `barre`, `open` (prima posizione, dove esiste), `jazz` (4 note), `triad` (3 corde alte) |
| `guitar` | `gretsch` | chitarra: `gretsch` (hollowbody), `epiphone` (solid body), `fender` (rock/hard rock), `acoustic` (acustica, ignora `amp`) (servono `setup <nome>`) |
| `amp` | dal groove | forza l'ampli: `clean` `blues` `twang` `crunch` `high` |
| `double` | dal groove | chitarra doppiata a sinistra e destra |
| `slapback` | dal groove | eco slapback rockabilly |
| `humanize` | `1.0` | 0 = perfettamente a tempo, 2 = molto "umano" |
| `strum_ms` | `14` | millisecondi tra una corda e l'altra nella pennata |
| `seed` | `1` | cambia per avere variazioni diverse di round robin e timing |

### Chiavi delle sezioni

| Chiave | Default | Descrizione |
|---|---|---|
| `name` | `Sezione N` | nome usato in `arrangement` |
| `chords` | — | battute (obbligatorio) |
| `repeat` | `1` | quante volte suonarla |
| `groove` | quello del brano | groove della sezione |
| `swing` | — | swing della sezione |
| `volume` | `1.0` | dinamica (es. `0.8` per una strofa più piano) |
| `fill` | `fills` | rullata a fine sezione |
| `guitar` / `drums` | `true` | `false` per togliere lo strumento nella sezione |

## 🎼 Come si legge una battuta

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

## 🎸 Accordi supportati

Tonica `A`…`G` con `#` o `b`, poi uno di questi suffissi, e un basso opzionale `/X` (es. `D/F#`):

| Tipo | Suffissi |
|---|---|
| maggiore / minore | *(niente)*, `m`, `min`, `-` |
| settime | `7`, `maj7`, `M7`, `m7`, `mmaj7`, `m7b5`, `ø`, `dim7`, `7sus4` |
| seste e none | `6`, `m6`, `9`, `m9`, `maj9`, `add9`, `13` |
| alterati | `7#9`, `7b9`, `7#5`, `aug`, `+`, `dim`, `°` |
| sospesi | `sus2`, `sus4` |
| power chord | `5` |

<!-- foot -->
---

<p align="center"><a href="tutorial.md">⬅ Precedente: 🎓 Tutorial</a> · <a href="#">⬆ Inizio pagina</a> · <a href="groove.md">Successiva: 🥁 Groove ➡</a></p>
<!-- /foot -->
