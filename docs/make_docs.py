"""Documentazione in due lingue (sito MkDocs, vedi mkdocs.yml): genera le pagine derivate dai dati.

    python3 docs/make_docs.py

- docs/{it,en}/grooves/   <- backingtrack.grooves.GROOVES (+ GROOVES_EN), una pagina per stile
- docs/{it,en}/examples/  <- examples/*/*.yaml, una pagina per stile
- docs/{it,en}/index.md    <- README.it.md / README.md (home del sito, link riscritti)
Le pagine hanno lo stesso nome nelle due lingue (mkdocs-static-i18n, struttura a cartelle).
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backingtrack.grooves import GROOVES  # noqa: E402
from backingtrack.locale_en import GROOVES_EN  # noqa: E402

REPO = "https://github.com/wdog/backingtrack/blob/main/"
STYLES = [("rock", "🤘", "Rock"), ("blues", "🎷", "Blues"), ("rockabilly", "🕺", "Rockabilly"), ("country", "🤠", "Country"),
          ("bluegrass", "🪕", "Bluegrass"),
          ("jazz", "🎺", "Jazz"), ("funk", "🪩", "Funk"), ("reggae", "🌴", "Reggae"), ("soul", "🎤", "Soul")]

def groove_pages(lang):
    """grooves/index.md (tabella degli stili) + grooves/<stile>.md."""
    it = lang == "it"
    pages = {}
    rows = []
    for key, emoji, name in STYLES:
        names = [n for n in GROOVES if n.split("/")[0] == key]
        rows.append("| [%s %s](%s.md) | %d |" % (emoji, name, key, len(names)))
        out = ["# %s\n" % name,
               ("%d groove. Si sceglie con `groove: %s` (o un altro nome della tabella) nel brano o nella sezione.\n"
                if it else "%d grooves. Pick one with `groove: %s` (or another name below) in the song or a section.\n")
               % (len(names), names[0]),
               "| Groove | %s |\n|---|---|---|---|---|" % (
                   "Ampli | Swing | Basso | Descrizione" if it else "Amp | Swing | Bass | Description")]
        for n in names:
            g = GROOVES[n]
            desc = g["desc"] if it else GROOVES_EN[n]
            desc = desc.split(":", 1)[1].strip() if ":" in desc else desc
            marks = (" 🎧" if g.get("double") else "") + (" 🔁" if g.get("slap") else "")
            out.append("| `%s` | %s%s | %g | %s | %s |" % (n, g["amp"], marks, g.get("swing", 0),
                                                         g.get("bass_style", ""), desc))
        pages["grooves/%s.md" % key] = "\n".join(out) + "\n"
    head = ("# Groove\n\n**%d groove** in %d stili. Ogni pagina elenca ampli, swing (0 = dritto, 1 = terzinato), basso "
            "(`--bass`) e descrizione;\n🎧 = chitarra doppiata L/R, 🔁 = slapback.\n\n| Stile | Groove |\n|---|---|\n"
            if it else
            "# Grooves\n\n**%d grooves** in %d styles. Each page lists amp, swing (0 = straight, 1 = triplet), bass "
            "(`--bass`) and description;\n🎧 = double-tracked guitar L/R, 🔁 = slapback.\n\n| Style | Grooves |\n|---|---|\n"
            ) % (len(GROOVES), len(STYLES))
    pages["grooves/index.md"] = head + "\n".join(rows) + "\n"
    return pages


def song_pages(lang):
    """examples/index.md (tabella degli stili) + examples/<stile>.md."""
    it = lang == "it"
    files = sorted(ROOT.glob("examples/*/*.yaml"))
    pages = {}
    rows = []
    for key, emoji, name in STYLES:
        group = [f for f in files if f.parent.name == key]
        if not group:
            continue
        rows.append("| [%s %s](%s.md) | %d |" % (emoji, name, key, len(group)))
        out = ["# %s\n" % name,
               "```sh\nbackingtrack render examples/%s/*.yaml --mp3     # %s\n```\n" % (key, "tutti" if it else "all of them"),
               "| %s |\n|---|---|---|---|" % ("File | Brano | BPM | Groove" if it else "File | Song | BPM | Groove")]
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
            out.append("| [`%s`](%sexamples/%s/%s) | %s | %s | %s |" % (
                f.stem, REPO, key, f.name, title, d.get("tempo", 120), ", ".join("`%s`" % g for g in grooves)))
        pages["examples/%s.md" % key] = "\n".join(out) + "\n"
    head = ("# Brani di esempio\n\nIn `examples/` ci sono **%d brani** divisi per stile. Contengono **solo la progressione "
            "di accordi**\n(niente melodia né testo), a scopo didattico; tempi e tonalità sono quelli più comuni o "
            "semplificati.\n\n| Stile | Brani |\n|---|---|\n" if it else
            "# Example songs\n\n`examples/` holds **%d songs** grouped by style. They contain **only the chord "
            "progression**\n(no melody or lyrics), for practice; tempos and keys are the most common or simplified ones.\n\n"
            "| Style | Songs |\n|---|---|\n") % len(files)
    pages["examples/index.md"] = head + "\n".join(rows) + "\n"
    return pages


def index_page(lang):
    """Home del sito = README della lingua, con i link riportati dentro docs/<lang>/."""
    text = (ROOT / ("README.it.md" if lang == "it" else "README.md")).read_text(encoding="utf-8")
    text = re.sub(r'<p align="center">[^\n]*README[^\n]*</p>\n+', "", text)  # cambio lingua: lo fa il sito
    # immagini in markdown: mkdocs riscrive i loro percorsi, quelli dell'HTML no
    text = re.sub(r'<p align="center">\s*<img src="docs/([^"]+)" alt="([^"]*)"[^>]*>\s*</p>', r"![\2](../\1)", text)
    text = re.sub(r"\]\((?!https?:|#|\.\./)([^)]+)\)", lambda m: "](%s%s)" % (REPO, m.group(1)), text)
    # senza menu laterale; titolo nascosto (altrimenti Material aggiunge "Home" sopra il logo)
    return "---\nhide:\n  - navigation\n---\n\n# backingtrack { .sr-only }\n\n" + text


def main():
    for lang in ("it", "en"):
        pages = dict(groove_pages(lang), **song_pages(lang), **{"index.md": index_page(lang)})
        for name, text in pages.items():
            path = ROOT / "docs" / lang / name
            path.parent.mkdir(exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print("✓", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
