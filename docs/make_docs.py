"""Documentazione in due lingue: genera le tabelle di groove e brani e la navigazione di ogni pagina.

    python3 docs/make_docs.py

- docs/it/groove.md, docs/en/grooves.md   <- backingtrack.grooves.GROOVES (+ GROOVES_EN)
- docs/it/brani.md,  docs/en/songs.md     <- examples/*/*.yaml
- in cima e in fondo a ogni pagina di docs/it e docs/en: menu, cambio lingua e pagina precedente/successiva
  (tra i commenti <!-- nav --> e <!-- foot -->, riscritti a ogni esecuzione).
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backingtrack.grooves import GROOVES  # noqa: E402
from backingtrack.locale_en import GROOVES_EN  # noqa: E402

# (chiave, file italiano, file inglese, titolo italiano, titolo inglese)
PAGES = [
    ("install", "installazione.md", "installation.md", "📦 Installazione", "📦 Installation"),
    ("gui", "gui.md", "gui.md", "🖥️ Editor grafico", "🖥️ Graphical editor"),
    ("tutorial", "tutorial.md", "tutorial.md", "🎓 Tutorial", "🎓 Tutorial"),
    ("format", "formato.md", "format.md", "📝 Formato", "📝 Song format"),
    ("grooves", "groove.md", "grooves.md", "🥁 Groove", "🥁 Grooves"),
    ("songs", "brani.md", "songs.md", "📚 Brani", "📚 Songs"),
    ("commands", "comandi.md", "commands.md", "⌨️ Comandi", "⌨️ Commands"),
    ("faq", "faq.md", "faq.md", "❓ FAQ", "❓ FAQ"),
    ("dev", "sviluppo.md", "development.md", "⚙️ Sviluppo", "⚙️ Development"),
]
STYLES = [("rock", "🤘", "Rock"), ("blues", "🎷", "Blues"), ("rockabilly", "🕺", "Rockabilly"), ("country", "🤠", "Country"),
          ("jazz", "🎺", "Jazz"), ("funk", "🪩", "Funk"), ("reggae", "🌴", "Reggae"), ("soul", "🎤", "Soul")]
TXT = {
    "it": dict(home="🏠 Home", readme="../../README.it.md", prev="Precedente", next="Successiva", top="⬆ Inizio pagina",
               other="🇬🇧 English", other_dir="en", here="🇮🇹 Italiano"),
    "en": dict(home="🏠 Home", readme="../../README.md", prev="Previous", next="Next", top="⬆ Back to top",
               other="🇮🇹 Italiano", other_dir="it", here="🇬🇧 English"),
}


def nav(lang, i):
    t = TXT[lang]
    col = 1 if lang == "it" else 2
    links = ["<a href=\"%s\">%s</a>" % (t["readme"], t["home"])]
    for j, p in enumerate(PAGES):
        title = p[3] if lang == "it" else p[4]
        links.append("<b>%s</b>" % title if j == i else "<a href=\"%s\">%s</a>" % (p[col], title))
    other = PAGES[i][2 if lang == "it" else 1]
    return ("<!-- nav -->\n<p align=\"center\">\n  %s\n</p>\n<p align=\"center\"><b>%s</b> · <a href=\"../%s/%s\">%s</a></p>\n"
            "<!-- /nav -->" % (" ·\n  ".join(links), t["here"], t["other_dir"], other, t["other"]))


def foot(lang, i):
    t = TXT[lang]
    col = 1 if lang == "it" else 2
    title = lambda p: p[3] if lang == "it" else p[4]
    parts = []
    if i > 0:
        parts.append("<a href=\"%s\">⬅ %s: %s</a>" % (PAGES[i - 1][col], t["prev"], title(PAGES[i - 1])))
    parts.append("<a href=\"#\">%s</a>" % t["top"])
    if i < len(PAGES) - 1:
        parts.append("<a href=\"%s\">%s: %s ➡</a>" % (PAGES[i + 1][col], t["next"], title(PAGES[i + 1])))
    return "<!-- foot -->\n---\n\n<p align=\"center\">%s</p>\n<!-- /foot -->" % " · ".join(parts)


def groove_page(lang):
    it = lang == "it"
    head = ("# 🥁 Groove disponibili\n\n%d groove in %d stili. Colonne: ampli, swing (0 = dritto, 1 = terzinato), basso "
            "(`--bass`) e descrizione;\n🎧 = chitarra doppiata L/R, 🔁 = slapback. Un groove si sceglie con `groove:` nel brano, "
            "anche sezione per sezione." if it else
            "# 🥁 Available grooves\n\n%d grooves in %d styles. Columns: amp, swing (0 = straight, 1 = triplet), bass "
            "(`--bass`) and description;\n🎧 = double-tracked guitar L/R, 🔁 = slapback. Pick a groove with `groove:` in the "
            "song, also section by section.") % (len(GROOVES), len(STYLES))
    out = [head]
    for key, emoji, name in STYLES:
        names = [n for n in GROOVES if n.split("/")[0] == key]
        out.append("<details>\n<summary><b>%s %s</b> — %d groove%s</summary>\n" % (emoji, name, len(names),
                                                                                "" if it or len(names) == 1 else "s"))
        out.append("| Groove | %s |\n|---|---|---|---|---|" % (
            "Ampli | Swing | Basso | Descrizione" if it else "Amp | Swing | Bass | Description"))
        for n in names:
            g = GROOVES[n]
            desc = g["desc"] if it else GROOVES_EN[n]
            desc = desc.split(":", 1)[1].strip() if ":" in desc else desc
            marks = (" 🎧" if g.get("double") else "") + (" 🔁" if g.get("slap") else "")
            out.append("| `%s` | %s%s | %g | %s | %s |" % (n, g["amp"], marks, g.get("swing", 0), g.get("bass_style", ""),
                                                         desc))
        out.append("\n</details>\n")
    return "\n\n".join(out[:1]) + "\n\n" + "\n".join(out[1:])


def songs_page(lang):
    it = lang == "it"
    files = sorted(ROOT.glob("examples/*/*.yaml"))
    out = [("# 📚 Brani di esempio inclusi\n\nIn `examples/` ci sono **%d brani** divisi per stile. Contengono **solo la "
            "progressione di accordi**\n(niente melodia né testo), a scopo didattico; tempi e tonalità sono quelli più comuni "
            "o semplificati.\n\n```sh\nbackingtrack render examples/rockabilly/*.yaml --mp3     # tutto il rockabilly\n```\n"
            if it else
            "# 📚 Included example songs\n\n`examples/` holds **%d songs** grouped by style. They contain **only the chord "
            "progression**\n(no melody or lyrics), for practice; tempos and keys are the most common or simplified ones.\n\n"
            "```sh\nbackingtrack render examples/rockabilly/*.yaml --mp3     # all the rockabilly\n```\n") % len(files)]
    for key, emoji, name in STYLES:
        group = [f for f in files if f.parent.name == key]
        if not group:
            continue
        out.append("<details>\n<summary><b>%s %s</b> — %d %s</summary>\n" % (emoji, name, len(group),
                                                                         "brani" if it else "songs"))
        out.append("| %s |\n|---|---|---|---|" % ("File | Brano | BPM | Groove" if it else "File | Song | BPM | Groove"))
        for f in group:
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
            title = str(d.get("title", f.stem))
            m = re.match(r"(.*?)\s*\((.*)\)$", title)
            if m:
                note = m.group(2) if it else {"in stile": "in the style", "progressione": "progression"}.get(m.group(2),
                                                                                                          m.group(2))
                title = "%s *(%s)*" % (m.group(1), note)
            grooves = [d.get("groove", "rock")] + [s.get("groove") for s in d.get("sections", []) if s.get("groove")]
            grooves = list(dict.fromkeys(grooves))
            out.append("| [`%s`](../../examples/%s/%s) | %s | %s | %s |" % (
                f.stem, key, f.name, title, d.get("tempo", 120), ", ".join("`%s`" % g for g in grooves)))
        out.append("\n</details>\n")
    return out[0] + "\n" + "\n".join(out[1:])


def with_nav(text, lang, i):
    text = re.sub(r"<!-- nav -->.*?<!-- /nav -->\n*", "", text, flags=re.S)
    text = re.sub(r"\n*<!-- foot -->.*?<!-- /foot -->\n*", "\n", text, flags=re.S)
    first, _, rest = text.partition("\n")
    return "%s\n\n%s\n\n%s\n\n%s\n" % (first, nav(lang, i), rest.strip("\n"), foot(lang, i))


def main():
    gen = {("it", "grooves"): groove_page("it"), ("en", "grooves"): groove_page("en"),
           ("it", "songs"): songs_page("it"), ("en", "songs"): songs_page("en")}
    for lang in ("it", "en"):
        for i, page in enumerate(PAGES):
            path = ROOT / "docs" / lang / page[1 if lang == "it" else 2]
            text = gen.get((lang, page[0]))
            if text is None:
                if not path.exists():
                    print("manca", path)
                    continue
                text = path.read_text(encoding="utf-8")
            path.write_text(with_nav(text, lang, i), encoding="utf-8")
            print("✓", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
