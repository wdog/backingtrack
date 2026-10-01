# 🖥️ Editor grafico

<!-- nav -->
<p align="center">
  <a href="../../README.it.md">🏠 Home</a> ·
  <a href="installazione.md">📦 Installazione</a> ·
  <b>🖥️ Editor grafico</b> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="formato.md">📝 Formato</a> ·
  <a href="groove.md">🥁 Groove</a> ·
  <a href="brani.md">📚 Brani</a> ·
  <a href="comandi.md">⌨️ Comandi</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="sviluppo.md">⚙️ Sviluppo</a>
</p>
<p align="center"><b>🇮🇹 Italiano</b> · <a href="../en/gui.md">🇬🇧 English</a></p>
<!-- /nav -->

```sh
backingtrack gui                 # nuovo brano
backingtrack gui mio_brano.yaml  # apri un brano
```

Su Linux l'installer aggiunge anche la voce **backingtrack** nel menu delle applicazioni.

<p align="center"><img src="../gui-sezioni-it.jpg" alt="editor: pagina Sezioni" width="900"></p>

La finestra ha tre schede (**Brano**, **Sezioni**, **YAML**) e mostra solo l'essenziale: il pulsante **⚙ Avanzate**
(o Brano ▸ Impostazioni avanzate) apre le impostazioni di dettaglio, e la scelta viene ricordata. Le spiegazioni
stanno nei tooltip: passa col mouse su una voce per leggerle. Tema scuro in stile [Dracula](https://draculatheme.com),
con accento viola e rosa.

**🌐 Lingua**: Aiuto ▸ Lingua / Language ▸ 🇮🇹 Italiano · 🇬🇧 English. L'editor si riavvia nella lingua scelta e
riprende il brano da dove eri (modifiche non salvate comprese). La prima volta usa la lingua del sistema.

## 🎵 Brano

Titolo, tempo, groove, basso e l'**ordine delle sezioni** (con ripetizioni e durata totale; lista vuota = ordine
della pagina Sezioni). Tra le avanzate: chitarra (Gretsch, Epiphone, Fender, acustica) e ampli, doppiatura,
slapback, voicing, conteggio, finale, rullate, trasposizione, swing, umanizzazione e output. Ogni scelta ha il suo
menu e non si può inserire un valore fuori scala.

Il **groove** si sceglie da un menu diviso per stile (🤘 Rock, 🎷 Blues, 🕺 Rockabilly, 🤠 Country, 🎺 Jazz,
🪩 Funk, 🌴 Reggae, 🎤 Soul), con una breve descrizione di ogni voce; quella completa compare sotto il menu.

<p align="center"><img src="../gui-brano-it.jpg" alt="editor: pagina Brano" width="700"></p>

## 🧩 Sezioni

Il cuore dell'editor, su tre colonne:

- **a sinistra** l'elenco delle sezioni, ognuna col suo colore e l'emoji dello stile; la sezione aperta è
  evidenziata col gradiente viola-rosa. Sotto: **Nuova** e i pulsanti per duplicare, riordinare ed eliminare;
- **al centro** due schede, **Accordi** e **Scale** (vedi sotto);
- **a destra** le impostazioni della sezione (nome, ripetizioni, groove; tra le avanzate dinamica, swing, rullata,
  strumenti) e i **modelli di giro**.

Per avere più spazio: **←** in cima all'elenco delle sezioni lo chiude (**Sezioni →** nella riga delle schede lo
riapre, oppure `F9`); allo stesso modo **→** in cima alla colonna di destra la chiude (**← Impostazioni** la riapre,
oppure `Shift+F9`). Con la finestra stretta (es. affiancata a metà schermo) l'elenco diventa a scomparsa e le
colonne si impilano.

### 🎼 Accordi

- Scrivi gli accordi direttamente nelle battute. Il pulsante ⓘ mostra esempi di battute e di accordi
  (Do Re Mi = C D E); la sintassi è spiegata in [Formato](formato.md#-come-si-legge-una-battuta).
- Sulla stessa riga: a sinistra gli accordi **usati nel brano**, a destra la **🎨 tavolozza** con le **12 note**
  (naturali sopra, più chiare; sotto ognuna la sua alterazione, più scura come i tasti neri: Db sotto C, F# sotto
  F…). **Clic** = aggiungi alla battuta selezionata (se nessuna è selezionata ne crea una nuova); **trascina** su
  una battuta per metterlo lì. Una nota è un accordo maggiore: m, 7, maj7… si aggiungono scrivendo nella battuta.
- Le battute sono una **griglia compatta** (4 per riga) col bordo nel colore della sezione. Trascina la maniglia
  `⠿` per **spostare una battuta**; il **tasto destro** per duplicarla, inserirne una prima/dopo, svuotarla o
  eliminarla; il `＋` in fondo per aggiungerne (ci puoi trascinare sopra un accordo). Passando col mouse leggi la
  battuta (*Em 2 tempi · D 1 · C 1*); se c'è un errore la cella diventa rossa e spiega cosa correggere.
- Pulsanti rapidi: duplica, `+ %` (ripeti la battuta precedente), `+ N.C.` (pausa), `+ vuota`, **Svuota**.

### 🎸 Scale

<p align="center"><img src="../gui-scale-it.jpg" alt="scheda Scale: tastiera con box CAGED e scale suggerite" width="900"></p>

Una **tastiera** (tasti 0–15, corda 1 in alto come nelle tablature) con le note della scala scelta, in qualsiasi
tonalità:

| Gruppo | Scale |
|---|---|
| 🎷 Pentatoniche e blues | pentatonica minore e maggiore, **blues minore** (1 b3 4 b5 5 b7), **blues maggiore** (1 2 b3 3 5 6) |
| 🎼 Maggiore e minori | maggiore, minore naturale, minore armonica, minore melodica |
| 🌈 Modi | dorico, misolidio, lidio, frigio |
| 🎸 Box blues | **B.B. King box** (1 2 b3 4 5 6, tonica sulla 2a corda; in A al 10° tasto) e **Albert King box** (1 b3 4 5 b7, in cima al 2° box della pentatonica minore), ognuno anche una corda sotto |

Le note sono scritte per lettera di grado (dorica di A = A B C D E F# G; la b5 di A è Eb, la #4 è D#) e hanno
quattro livelli di evidenza:

| Nota | Come appare |
|---|---|
| **tonica** | viola, più grande, con alone |
| **blue note** (nei modi: la nota caratteristica) | rosa |
| **terza e quinta** (le note dell'accordo) | azzurro pieno |
| altre note | cerchio vuoto |

- **Sistema CAGED**: il manico è diviso nei 5 box delle forme C, A, G, E, D (minori nelle scale minori), ognuno col
  suo colore. Clicca un box (o la sua fascia sulla tastiera) per vederlo da solo, poi i box accanto per unirli
  (es. Em + Dm = tasti 5–10); clic su quello all'estremità per toglierlo.
- **Etichette**: nomi delle note o gradi (1, b3, 5…), che valgono in ogni tonalità.
- **✨ Suggerite per «sezione»**: il riquadro in alto legge gli accordi della sezione aperta e propone le scale
  adatte; un clic imposta tonalità e scala. La tonalità è quella del primo accordo; poi riconosce i giri tipici:

  | Accordi | Proposta |
  |---|---|
  | I, IV, V con almeno una settima (`A7 D7 E7`, `A D7 E7`) | blues minore e maggiore, misolidia, box B.B. King e Albert King |
  | i minore + IV7 (`Am7 D7`) | dorica |
  | I + bVII (`A G D`) | misolidia |
  | i minore + bII (`Am Bb`) | frigia |
  | I + II maggiore (`D E`) | lidia |
  | i minore + V7 (`Am Dm E7`) | minore armonica |
  | altro | la tonalità che contiene più accordi (almeno 2/3; le settime sui gradi contano come dominanti secondarie) |

- **Segui accordi**: accendilo e premi ▶ (il pulsante compare solo in questa modalità). Mentre la base suona, le
  note dell'accordo della battuta corrente hanno un **anello giallo**, quelle fuori scala (es. il C# di A7 sulla
  blues minore) un **pallino giallo**, e il resto si attenua. Accanto al play: l'accordo e le sue note (`♪ A7  A C# E G`).

### ✨ Modelli di giro e tonalità

I **modelli di giro** (12-bar blues, 8-bar, blues minore, I-IV-V, anni '50, pop-rock…) sono scritti a gradi (I, IV,
V) e la **Tonalità** li trasforma in accordi veri: 12-bar blues in A = A7, D7, E7; in E = E7, A7, B7.
**Sostituisci accordi** cancella le battute della sezione e ci mette il giro, **Aggiungi in coda** lo mette dopo.
Nessuno dei due traspone: per spostare un brano già scritto c'è **Trasposizione** (Brano ▸ Avanzate).

**Tonica ≠ tonalità**: la *tonica* è la nota su cui è costruito **un accordo** (A in A7, D in D7); la *tonalità* è la
«casa» di **tutto il brano**. Il 12-bar blues in A (`A7 A7 A7 A7 | D7 D7 A7 A7 | E7 D7 A7 E7`) ha tre toniche, A, D
ed E, ma una sola tonalità: A, perché gira intorno ad A7 e finisce lì. Cambiando un accordo cambi una tonica;
cambiando la tonalità del modello cambi tutto il giro.

## 📄 YAML

Il file che verrà salvato, sempre aggiornato, da copiare con un clic.

## 🎧 Il player

In basso la **barra di stato** dice se il brano è pronto (✓ verde, con battute e durata) o cosa correggere (⚠).
**Genera e ascolta** (`Alt+G`) crea l'audio **anche se non hai salvato** e lo suona subito nel player, che compare
solo dopo la prima generazione:

- pulsanti **da capo**, **play/pausa**, **stop**, titolo, tempo e **battuta corrente**, nel brano e nella sezione
  (*Battuta 10 / 52 · Strofa 6 / 12*);
- la **forma d'onda** con una linea colorata dove inizia ogni sezione: clicca o trascina per spostarti;
- la **striscia degli accordi**: tutte le battute in fila, divise in proporzione ai tempi, col numero nel brano e
  nella sezione. La battuta che suona è evidenziata, la striscia scorre da sola e un clic su una battuta salta lì;
- il **🔁 loop** per studiare un passaggio: accendilo (`L`), scegli **da battuta X a battuta Y** e il player ripete
  solo quel tratto, segnato in rosa. **Shift+clic** su una battuta della striscia sposta la fine del loop;
- volume e cartella dei file generati (nascosti con la finestra stretta).

## ❓ Guida integrata

**Aiuto ▸ Guida** (`F1`) spiega ogni parte della finestra: Inizio, Brano, Sezioni, Accordi, Tonalità, Scale,
Player e Tasti.

<p align="center"><img src="../gui-guida-it.jpg" alt="guida integrata: pagina Tonalità" width="640"></p>

## 💾 Salvataggio e bozza automatica

File ▸ **Salva** (`Ctrl+S`) e **Salva con nome** (`Ctrl+Shift+S`) scrivono il file YAML. Se chiudi con modifiche non
salvate la finestra chiede cosa fare. In più ogni modifica finisce in una **bozza automatica**: se il programma si
chiude male o scegli "Non salvare" per sbaglio, alla riapertura ti propone di **ripristinarla**.
Il menu **File ▸ Apri esempio** carica al volo uno dei brani inclusi.

## ⌨️ Scorciatoie

| Tasto | Azione |
|---|---|
| `Ctrl+N` / `Ctrl+O` | nuovo / apri |
| `Ctrl+S` / `Ctrl+Shift+S` | salva / salva con nome |
| `Alt+G` (o `Ctrl+R`) | genera e ascolta |
| `Ctrl+T` / `Ctrl+D` | nuova sezione / duplica sezione |
| `Ctrl+B` o `Super+N` / `Ctrl+Shift+D` | nuova battuta / duplica battuta |
| `Super+Canc` | elimina la battuta selezionata |
| `F9` / `Shift+F9` | mostra / nasconde l'elenco delle sezioni / la colonna delle impostazioni |
| `Invio` (in una battuta) | passa alla battuta successiva (la crea se serve) |
| `Spazio` / `B` / `S` / `L` | play-pausa / da capo / stop / loop |
| `F1` | guida |
| `Ctrl+Q` | esci |

Spazio, B, S e L funzionano quando **non** stai scrivendo in un campo: così puoi digitare `Bb` o `Dsus4` senza
problemi.

<!-- foot -->
---

<p align="center"><a href="installazione.md">⬅ Precedente: 📦 Installazione</a> · <a href="#">⬆ Inizio pagina</a> · <a href="tutorial.md">Successiva: 🎓 Tutorial ➡</a></p>
<!-- /foot -->
