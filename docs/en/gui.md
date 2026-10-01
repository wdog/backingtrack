# 🖥️ Graphical editor

<!-- nav -->
<p align="center">
  <a href="../../README.md">🏠 Home</a> ·
  <a href="installation.md">📦 Installation</a> ·
  <b>🖥️ Graphical editor</b> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="format.md">📝 Song format</a> ·
  <a href="grooves.md">🥁 Grooves</a> ·
  <a href="songs.md">📚 Songs</a> ·
  <a href="commands.md">⌨️ Commands</a> ·
  <a href="faq.md">❓ FAQ</a> ·
  <a href="development.md">⚙️ Development</a>
</p>
<p align="center"><b>🇬🇧 English</b> · <a href="../it/gui.md">🇮🇹 Italiano</a></p>
<!-- /nav -->

```sh
backingtrack gui                 # new song
backingtrack gui my_song.yaml    # open a song
```

On Linux the installer also adds a **backingtrack** entry to the application menu.

<p align="center"><img src="../gui-sezioni-en.jpg" alt="editor: Sections page" width="900"></p>

The window has three tabs (**Song**, **Sections**, **YAML**) and shows only the essentials: the **⚙ Advanced** button
(or Song ▸ Advanced settings) opens the detailed settings, and the choice is remembered. Explanations live in the
tooltips: hover over an item to read them. Dark [Dracula](https://draculatheme.com) theme, with purple and pink accents.

**🌐 Language**: Help ▸ Language / Lingua ▸ 🇮🇹 Italiano · 🇬🇧 English. The editor restarts in the chosen language and
picks up the song where you left it (unsaved changes included). The first time it uses your system language.

## 🎵 Song

Title, tempo, groove, bass and the **section order** (with repeats and total length; empty list = order of the
Sections page). Among the advanced settings: guitar (Gretsch, Epiphone, Fender, acoustic) and amp, double tracking,
slapback, voicing, count-in, ending, drum fills, transpose, swing, humanize and output. Every choice has its own menu,
so an out-of-range value cannot be entered.

The **groove** is picked from a menu split by style (🤘 Rock, 🎷 Blues, 🕺 Rockabilly, 🤠 Country, 🎺 Jazz,
🪩 Funk, 🌴 Reggae, 🎤 Soul), with a short description of each item; the full one appears below the menu.

<p align="center"><img src="../gui-brano-en.jpg" alt="editor: Song page" width="700"></p>

## 🧩 Sections

The heart of the editor, in three columns:

- **on the left** the list of sections, each with its color and the emoji of its style; the open section is
  highlighted with the purple-pink gradient. Below: **New** and the buttons to duplicate, reorder and delete;
- **in the middle** two tabs, **Chords** and **Scales** (see below);
- **on the right** the section settings (name, repeats, groove; among the advanced ones dynamics, swing, fill,
  instruments) and the **progression templates**.

For more room: **←** at the top of the section list closes it (**Sections →** in the tab row reopens it, or `F9`);
likewise **→** at the top of the right column closes it (**← Settings** reopens it, or `Shift+F9`). With a narrow
window (e.g. tiled to half the screen) the list becomes a slide-in panel and the columns stack.

### 🎼 Chords

- Type the chords straight into the bars. The ⓘ button shows examples of bars and chords; the syntax is explained
  in [Song format](format.md#-reading-a-bar).
- On one row: on the left the chords **used in the song**, on the right the **🎨 palette** with the **12 notes**
  (naturals on top, lighter; under each one its accidental, darker like the black keys: Db under C, F# under F…).
  **Click** = add to the selected bar (if none is selected it creates a new one); **drag** onto a bar to put it there.
  A note is a major chord: m, 7, maj7… are added by typing in the bar.
- Bars are a **compact grid** (4 per row) bordered in the section color. Drag the `⠿` handle to **move a bar**;
  **right click** to duplicate it, insert one before/after, clear it or delete it; the `＋` at the end adds one (you
  can drop a chord on it). Hovering reads the bar back (*Em 2 beats · D 1 · C 1*); if there is an error the cell turns
  red and says what to fix.
- Quick buttons: duplicate, `+ %` (repeat the previous bar), `+ N.C.` (rest), `+ empty`, **Clear**.

### 🎸 Scales

<p align="center"><img src="../gui-scale-en.jpg" alt="Scales tab: fretboard with CAGED boxes and suggested scales" width="900"></p>

A **fretboard** (frets 0–15, string 1 on top as in tablature) with the notes of the chosen scale, in any key:

| Group | Scales |
|---|---|
| 🎷 Pentatonics and blues | minor and major pentatonic, **minor blues** (1 b3 4 b5 5 b7), **major blues** (1 2 b3 3 5 6) |
| 🎼 Major and minors | major, natural minor, harmonic minor, melodic minor |
| 🌈 Modes | Dorian, Mixolydian, Lydian, Phrygian |
| 🎸 Blues boxes | **B.B. King box** (1 2 b3 4 5 6, root on the 2nd string; in A at the 10th fret) and **Albert King box** (1 b3 4 5 b7, at the top of the 2nd minor pentatonic box), each one also a string lower |

Notes are spelled by scale degree (A Dorian = A B C D E F# G; the b5 of A is Eb, the #4 is D#) and have four levels
of emphasis:

| Note | Looks like |
|---|---|
| **root** | purple, bigger, with a halo |
| **blue note** (in the modes: the characteristic note) | pink |
| **third and fifth** (the chord tones) | filled light blue |
| other notes | hollow circle |

- **CAGED system**: the neck is split into the 5 boxes of the C, A, G, E, D shapes (minor in minor scales), each in
  its own color. Click a box (or its band on the fretboard) to see it alone, then the boxes next to it to join them
  (e.g. Em + Dm = frets 5–10); click the one at the edge to remove it.
- **Labels**: note names or degrees (1, b3, 5…), which are the same in every key.
- **✨ Suggested for "section"**: the box at the top reads the chords of the open section and proposes the right
  scales; one click sets key and scale. The key is the first chord; then it recognizes the typical progressions:

  | Chords | Suggestion |
  |---|---|
  | I, IV, V with at least one seventh (`A7 D7 E7`, `A D7 E7`) | minor and major blues, Mixolydian, B.B. King and Albert King boxes |
  | minor i + IV7 (`Am7 D7`) | Dorian |
  | I + bVII (`A G D`) | Mixolydian |
  | minor i + bII (`Am Bb`) | Phrygian |
  | I + major II (`D E`) | Lydian |
  | minor i + V7 (`Am Dm E7`) | harmonic minor |
  | anything else | the key that contains most chords (at least 2/3; sevenths on scale degrees count as secondary dominants) |

- **Follow chords**: turn it on and press ▶ (the button only appears in this mode). While the track plays, the notes of
  the current chord get a **yellow ring**, those outside the scale (e.g. the C# of A7 over the minor blues) a
  **yellow dot**, and the rest fades. Next to play: the chord and its notes (`♪ A7  A C# E G`).

### ✨ Progression templates and keys

The **progression templates** (12-bar blues, 8-bar, minor blues, I-IV-V, '50s, pop-rock…) are written in degrees
(I, IV, V) and the **Key** turns them into real chords: 12-bar blues in A = A7, D7, E7; in E = E7, A7, B7.
**Replace chords** clears the bars of the section and puts the progression in, **Append** adds it after them.
Neither one transposes: to move a song you already wrote there is **Transpose** (Song ▸ Advanced).

**Root ≠ key**: the *root* is the note **a chord** is built on (A in A7, D in D7); the *key* is the "home" of **the
whole song**. The 12-bar blues in A (`A7 A7 A7 A7 | D7 D7 A7 A7 | E7 D7 A7 E7`) has three roots, A, D and E, but only
one key: A, because it revolves around A7 and ends there. Changing a chord changes a root; changing the key of the
template changes the whole progression.

## 📄 YAML

The file that will be saved, always up to date, copied with one click.

## 🎧 The player

At the bottom the **status bar** says whether the song is ready (green ✓, with bars and length) or what to fix (⚠).
**Render & play** (`Alt+G`) creates the audio **even if you have not saved** and plays it right away in the player,
which appears after the first render:

- buttons **from the start**, **play/pause**, **stop**, title, time and **current bar**, in the song and in the
  section (*Bar 10 / 52 · Verse 6 / 12*);
- the **waveform** with a colored line where each section starts: click or drag to move;
- the **chord strip**: all the bars in a row, split in proportion to the beats, with their number in the song and in
  the section. The bar being played is highlighted, the strip scrolls by itself and clicking a bar jumps there;
- the **🔁 loop** to practice a passage: turn it on (`L`), choose **from bar X to bar Y** and the player repeats only
  that range, marked in pink. **Shift+click** on a bar of the strip moves the end of the loop;
- volume and output folder (hidden with a narrow window).

## ❓ Built-in guide

**Help ▸ Guide** (`F1`) explains every part of the window: Start, Song, Sections, Chords, Key, Scales, Player and Keys.

<p align="center"><img src="../gui-guida-en.jpg" alt="built-in guide" width="640"></p>

## 💾 Saving and automatic draft

File ▸ **Save** (`Ctrl+S`) and **Save as** (`Ctrl+Shift+S`) write the YAML file. If you close with unsaved changes the
window asks what to do. On top of that every change goes into an **automatic draft**: if the program crashes or you
pick "Don't save" by mistake, it offers to **restore it** at the next start.
The **File ▸ Open example** menu loads one of the included songs.

## ⌨️ Shortcuts

| Key | Action |
|---|---|
| `Ctrl+N` / `Ctrl+O` | new / open |
| `Ctrl+S` / `Ctrl+Shift+S` | save / save as |
| `Alt+G` (or `Ctrl+R`) | render and play |
| `Ctrl+T` / `Ctrl+D` | new section / duplicate section |
| `Ctrl+B` or `Super+N` / `Ctrl+Shift+D` | new bar / duplicate bar |
| `Super+Delete` | delete the selected bar |
| `F9` / `Shift+F9` | show / hide the section list / the settings column |
| `Enter` (in a bar) | go to the next bar (creates it if needed) |
| `Space` / `B` / `S` / `L` | play-pause / from the start / stop / loop |
| `F1` | guide |
| `Ctrl+Q` | quit |

Space, B, S and L work when you are **not** typing in a field: so you can type `Bb` or `Dsus4` without trouble.

<!-- foot -->
---

<p align="center"><a href="installation.md">⬅ Previous: 📦 Installation</a> · <a href="#">⬆ Back to top</a> · <a href="tutorial.md">Next: 🎓 Tutorial ➡</a></p>
<!-- /foot -->
