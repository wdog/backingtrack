# ❓ FAQ e problemi comuni

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
  <b>❓ FAQ</b> ·
  <a href="sviluppo.md">⚙️ Sviluppo</a>
</p>
<p align="center"><b>🇮🇹 Italiano</b> · <a href="../en/faq.md">🇬🇧 English</a></p>
<!-- /nav -->

<details>
<summary><b>"campioni '...' non installati"</b></summary>

Esegui `backingtrack setup`. Con `--bass` serve anche `backingtrack setup bass`, con `guitar: epiphone` serve `backingtrack setup epiphone`.
</details>

<details>
<summary><b>"ffmpeg non trovato nel PATH"</b></summary>

Installa ffmpeg (vedi [Installazione](installazione.md)) e riapri il terminale. `backingtrack doctor` verifica.
</details>

<details>
<summary><b>"backingtrack gui" non parte</b></summary>

Lancia `backingtrack doctor` e guarda la riga **GUI**. Di solito mancano GTK 4 e libadwaita (il comando per
installarli è nel riepilogo finale). Se sono installati ma il programma non li vede, è stato installato con pipx
senza `--system-site-packages`: `backingtrack update` o l'installer lo reinstallano nel modo giusto.
</details>

<details>
<summary><b>Come cambio lingua?</b></summary>

Nell'editor: **Aiuto ▸ Lingua / Language** (🇮🇹 Italiano · 🇬🇧 English); l'editor si riavvia e tiene il brano.
L'inglese è la lingua predefinita; da riga di comando usa `BACKINGTRACK_LANG=it` per l'italiano.
</details>

<details>
<summary><b>Genera senza salvare?</b></summary>

Sì: **Genera e ascolta** usa il brano così com'è nell'editor, salvato o no. Il file audio finisce nella cartella
di output (scheda Brano, default `out/`).
</details>

<details>
<summary><b>Posso usare il MIDI in una DAW?</b></summary>

Sì: ogni render crea anche `out/<nome>.mid` con tracce separate (Guitar L/R, Bass, Drums, batteria in mappa GM).
Con `--midi-only` ottieni solo quello.
</details>

<details>
<summary><b>Il 3/4 o il 6/8?</b></summary>

Per ora solo 4/4. Il feel in 12/8 si ottiene con `blues/slow` (terzine) o con `swing: 1`.
</details>

<details>
<summary><b>Come ottengo variazioni diverse dello stesso brano?</b></summary>

Cambia `seed` nel file: cambiano round robin, micro-timing e dinamiche.
</details>

<details>
<summary><b>Il download dei campioni si interrompe</b></summary>

Rilancia `backingtrack setup` (o `backingtrack update`): i pacchetti già completi vengono saltati.
</details>

<!-- foot -->
---

<p align="center"><a href="comandi.md">⬅ Precedente: ⌨️ Comandi</a> · <a href="#">⬆ Inizio pagina</a> · <a href="sviluppo.md">Successiva: ⚙️ Sviluppo ➡</a></p>
<!-- /foot -->
