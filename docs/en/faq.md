# ❓ FAQ and common problems

<!-- nav -->
<p align="center">
  <a href="../../README.md">🏠 Home</a> ·
  <a href="installation.md">📦 Installation</a> ·
  <a href="gui.md">🖥️ Graphical editor</a> ·
  <a href="tutorial.md">🎓 Tutorial</a> ·
  <a href="format.md">📝 Song format</a> ·
  <a href="grooves.md">🥁 Grooves</a> ·
  <a href="songs.md">📚 Songs</a> ·
  <a href="commands.md">⌨️ Commands</a> ·
  <b>❓ FAQ</b> ·
  <a href="development.md">⚙️ Development</a>
</p>
<p align="center"><b>🇬🇧 English</b> · <a href="../it/faq.md">🇮🇹 Italiano</a></p>
<!-- /nav -->

<details>
<summary><b>"'...' samples not installed"</b></summary>

Run `backingtrack setup`. With `--bass` you also need `backingtrack setup bass`, with `guitar: epiphone` you need
`backingtrack setup epiphone`.
</details>

<details>
<summary><b>"ffmpeg not found in PATH"</b></summary>

Install ffmpeg (see [Installation](installation.md)) and reopen the terminal. `backingtrack doctor` checks it.
</details>

<details>
<summary><b>"backingtrack gui" does not start</b></summary>

Run `backingtrack doctor` and look at the **GUI** line. Usually GTK 4 and libadwaita are missing (the command to
install them is in the final summary). If they are installed but the program does not see them, it was installed with
pipx without `--system-site-packages`: `backingtrack update` or the installer reinstall it the right way.
</details>

<details>
<summary><b>How do I switch the language?</b></summary>

In the editor: **Help ▸ Language / Lingua** (🇮🇹 Italiano · 🇬🇧 English); the editor restarts and keeps your song.
English is the default; on the command line use `BACKINGTRACK_LANG=it` for Italian.
</details>

<details>
<summary><b>Render without saving?</b></summary>

Yes: **Render & play** uses the song as it is in the editor, saved or not. The audio file goes to the output folder
(Song tab, default `out/`).
</details>

<details>
<summary><b>Can I use the MIDI in a DAW?</b></summary>

Yes: every render also creates `out/<name>.mid` with separate tracks (Guitar L/R, Bass, Drums, drums in GM mapping).
With `--midi-only` you get just that.
</details>

<details>
<summary><b>3/4 or 6/8?</b></summary>

4/4 only for now. A 12/8 feel comes from `blues/slow` (triplets) or `swing: 1`.
</details>

<details>
<summary><b>How do I get different variations of the same song?</b></summary>

Change `seed` in the file: round robins, micro-timing and dynamics change.
</details>

<details>
<summary><b>The sample download stops</b></summary>

Run `backingtrack setup` (or `backingtrack update`) again: packs that are already complete are skipped.
</details>

<!-- foot -->
---

<p align="center"><a href="commands.md">⬅ Previous: ⌨️ Commands</a> · <a href="#">⬆ Back to top</a> · <a href="development.md">Next: ⚙️ Development ➡</a></p>
<!-- /foot -->
