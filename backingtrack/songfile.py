"""Modello del brano per l'editor: valori di default, validazione, modelli di giro e scrittura YAML.

Niente GTK qui: tutto è testabile e riusabile.
"""
import re

import yaml

from .errors import SongError
from .grooves import GROOVES
from .song import build_timeline
from .theory import FLAT_NAMES, NOTE_PC, SHARP_NAMES, Chord

# chiave -> default (None = "dal groove")
SONG_DEFAULTS = {
    "title": "Nuova canzone", "tempo": 120, "groove": "blues", "transpose": 0, "swing": None,
    "guitar": "gretsch", "amp": None, "double": None, "slapback": None, "bass": False,
    "count_in": True, "ending": True, "ending_chord": None, "fills": True, "crash": True,
    "humanize": 1.0, "strum_ms": 14, "seed": 1,
}
SECTION_DEFAULTS = {"repeat": 1, "groove": None, "swing": None, "volume": 1.0,
                    "fill": None, "guitar": True, "drums": True}
KEY_ORDER = list(SONG_DEFAULTS)

ROOTS = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"]
KEYS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
# (suffisso, descrizione) — gli accordi principali, in ordine d'uso
QUALITY_CHOICES = [
    ("", "maggiore"), ("m", "minore"), ("7", "settima"), ("5", "power chord"),
    ("maj7", "settima maggiore"), ("m7", "minore settima"), ("6", "sesta"), ("m6", "minore sesta"),
    ("9", "nona"), ("m9", "minore nona"), ("add9", "add9"), ("13", "tredicesima"), ("7#9", "7#9 (Hendrix)"),
    ("sus2", "sus2"), ("sus4", "sus4"), ("7sus4", "7sus4"), ("dim", "diminuito"), ("dim7", "diminuito 7"),
    ("m7b5", "semidiminuito"), ("aug", "aumentato"),
]
AMPS = ["clean", "blues", "twang", "crunch", "high"]
GUITARS = ["gretsch", "epiphone", "archtop", "archtop_mic"]
BASSES = [False, True, "ebass", "sneakybass"]  # valori di `bass:` (true = contrabbasso)
FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb"}

# modelli: (nome, [battute con gradi]) — gradi: I bIII IV V bVI bVII ii iii vi, suffissi dopo ":"
TEMPLATES = {
    "12-bar blues (quick change)": "I:7 IV:7 I:7 I:7 | IV:7 IV:7 I:7 I:7 | V:7 IV:7 I:7 V:7",
    "12-bar blues": "I:7 I:7 I:7 I:7 | IV:7 IV:7 I:7 I:7 | V:7 IV:7 I:7 V:7",
    "8-bar blues": "I V:7 IV IV | I V:7 I,IV I,V:7",
    "Blues minore": "I:m7 IV:m7 I:m7 I:m7 | IV:m7 IV:m7 I:m7 I:m7 | bVI:7 V:7 I:m7 V:7",
    "Slow blues con passaggi": "I:7 IV:7 I:7 I:7 | IV:7 IV:7 I:7 I:7 | V:7 IV:7 I:7,IV:7 I:7,V:7",
    "Rock'n'roll I-IV-V (12)": "I I I I | IV IV I I | V IV I V",
    "Anni '50 I-vi-IV-V": "I vi:m IV V",
    "Pop-rock I-V-vi-IV": "I V vi:m IV",
    "Rock I-bVII-IV": "I bVII IV I",
    "Minore i-bVII-bVI-V": "I:m bVII bVI V",
    "Turnaround I-IV-I-V": "I:7 IV:7 I:7 V:7",
    "Un accordo (boogie)": "I:7 I:7 I:7 I:7",
}
DEGREES = {"I": 0, "bII": 1, "ii": 2, "II": 2, "bIII": 3, "iii": 4, "III": 4, "IV": 5, "#IV": 6, "V": 7,
           "bVI": 8, "vi": 9, "VI": 9, "bVII": 10, "VII": 11, "vii": 11}


def chord_name(key, degree, suffix=""):
    pc = (NOTE_PC[key[0]] + {"#": 1, "b": -1}.get(key[1:], 0) + DEGREES[degree]) % 12
    return (FLAT_NAMES if key in FLAT_KEYS else SHARP_NAMES)[pc] + suffix


def template_bars(name, key):
    """Battute (testo) di un modello nella tonalità scelta."""
    bars = []
    for cell in TEMPLATES[name].replace("|", " ").split():
        chords = []
        for part in cell.split(","):
            deg, _, suf = part.partition(":")
            chords.append(chord_name(key, deg, suf))
        bars.append(" ".join(chords))
    return bars


# ------------------------------------------------------------------ validazione

def check_chord(token):
    """None se il simbolo è valido, altrimenti il messaggio d'errore."""
    try:
        Chord(token)
        return None
    except SongError as e:
        return str(e)


HOLD = (".", "-", "/")
BAR_HELP = ("Ogni battuta ha 4 tempi, divisi in parti uguali tra i simboli scritti. "
            "'.' prolunga l'accordo precedente di una parte: 'Em . D C' = Em per 2 tempi, D per 1, C per 1. "
            "'%' ripete la battuta precedente, 'N.C.' = pausa della chitarra.")


def _beats(x):
    whole, frac = int(x), round(x - int(x), 3)
    frac_s = {0.333: "⅓", 0.5: "½", 0.667: "⅔", 0.25: "¼", 0.75: "¾"}.get(frac, "")
    return (str(whole) if whole else "") + frac_s if frac_s else str(whole)


def describe_bar(text, first=False):
    """Lettura in parole di una battuta: 'Em . D C' -> 'Em 2 tempi · D 1 · C 1'."""
    if check_bar(text, first):
        return None
    toks = text.split()
    if toks == ["%"]:
        return "ripete la battuta precedente"
    step = 4 / len(toks)
    parts = []
    for t in toks:
        if t in HOLD:
            parts[-1][1] += step
        else:
            parts.append([("pausa" if t.upper() in ("N.C.", "NC") else t), step])
    if len(parts) == 1:
        return "%s per tutta la battuta" % parts[0][0]
    out = ["%s %s %s" % (parts[0][0], _beats(parts[0][1]), "tempo" if parts[0][1] == 1 else "tempi")]
    out += ["%s %s" % (n, _beats(d)) for n, d in parts[1:]]
    return " · ".join(out)


def check_bar(text, first=False):
    """Valida il testo di una battuta ('A7', 'C . G .', '%', 'N.C.'). None = ok, altrimenti un messaggio chiaro."""
    toks = text.split()
    if not toks:
        return "battuta vuota: scrivi un accordo (es. A7), '%' per ripetere la precedente o 'N.C.' per una pausa"
    if toks == ["%"]:
        return ("'%' ripete la battuta precedente, ma questa è la prima della sezione: scrivi un accordo"
                if first else None)
    if "%" in toks:
        return "'%' deve stare da solo nella battuta (ripete tutta la battuta precedente)"
    if len(toks) > 4:
        return "al massimo 4 simboli per battuta, uno per tempo (es. 'C G Am F')"
    if toks[0] in HOLD:
        return ("'%s' prolunga l'accordo precedente, quindi non può aprire la battuta. "
                "Esempio: 'Em . D C' = Em per 2 tempi, D per 1, C per 1" % toks[0])
    for t in toks:
        if t in HOLD or t.upper() in ("N.C.", "NC"):
            continue
        err = check_chord(t)
        if err:
            return err + chord_hint(t)
    return None


def chord_hint(token):
    """Suggerimento per un simbolo sbagliato."""
    if token[:1].islower() and token[:1].upper() in NOTE_PC:
        return ": la tonica va maiuscola (es. '%s')" % (token[0].upper() + token[1:])
    if token[:1] == "H":
        return ": in notazione inglese il Si è B (es. 'B7')"
    if token[:1].upper() not in NOTE_PC:
        return ": un accordo inizia con una nota A B C D E F G (es. 'Am', 'F#7', 'Bb')"
    return ": tipi validi: m, 7, maj7, m7, 5, 6, 9, sus4, dim, aug… (es. 'Am7', 'Dsus4')"


def split_bars(chords):
    return [c.strip() for c in re.split(r"[|\n]", str(chords or "")) if c.strip()]


def validate(song):
    """Lista di errori leggibili (vuota se il brano è valido)."""
    errors = []
    names = [s.get("name", "") for s in song.get("sections", [])]
    if not names:
        errors.append("aggiungi almeno una sezione")
    for i, sec in enumerate(song.get("sections", [])):
        name = sec.get("name") or ""
        if not name.strip():
            errors.append("sezione %d: manca il nome" % (i + 1))
        elif names.count(name) > 1:
            errors.append("sezione '%s': nome ripetuto" % name)
        bars = sec.get("bars", [])
        if not bars:
            errors.append("sezione '%s': nessuna battuta" % name)
        for j, bar in enumerate(bars):
            err = check_bar(bar, j == 0)
            if err:
                errors.append("sezione '%s', battuta %d: %s" % (name, j + 1, err))
    if song.get("ending_chord"):
        err = check_chord(song["ending_chord"])
        if err:
            errors.append("accordo finale: %s" % err)
    for item in song.get("arrangement") or []:
        if item["section"] not in names:
            errors.append("arrangiamento: la sezione '%s' non esiste" % item["section"])
    if not errors:
        try:
            build_timeline(to_song_dict(song))
        except SongError as e:
            errors.append(str(e))
    return errors


# ------------------------------------------------------------------ conversioni

def new_song():
    song = {k: v for k, v in SONG_DEFAULTS.items()}
    song["sections"] = [dict(SECTION_DEFAULTS, name="Strofa", repeat=2,
                             bars=template_bars("12-bar blues (quick change)", "A"))]
    song["tempo"] = 100
    song["arrangement"] = []
    return song


def from_song_dict(data):
    """Dict YAML (formato file) -> modello dell'editor (bars come lista di testi)."""
    song = {k: data.get(k, v) for k, v in SONG_DEFAULTS.items()}
    song["extra"] = {k: v for k, v in data.items() if k not in SONG_DEFAULTS and k not in ("sections", "arrangement")}
    song["sections"] = []
    for i, sec in enumerate(data.get("sections") or []):
        s = {k: sec.get(k, v) for k, v in SECTION_DEFAULTS.items()}
        s["name"] = str(sec.get("name", "Sezione %d" % (i + 1)))
        s["bars"] = split_bars(sec.get("chords"))
        song["sections"].append(s)
    song["arrangement"] = []
    for item in data.get("arrangement") or []:
        m = re.match(r"^(.*?)\s*[x×*]\s*(\d+)$", str(item).strip())
        name, reps = (m.group(1), int(m.group(2))) if m else (str(item).strip(), None)
        song["arrangement"].append({"section": name, "repeat": reps})
    return song


def to_song_dict(song):
    """Modello dell'editor -> dict nel formato file (solo i valori diversi dal default)."""
    out = {}
    for k in KEY_ORDER:
        v = song.get(k, SONG_DEFAULTS[k])
        if k in ("title", "tempo", "groove") or v != SONG_DEFAULTS[k]:
            if v is not None:
                out[k] = v
    out.update(song.get("extra") or {})
    out["sections"] = []
    for sec in song.get("sections", []):
        s = {"name": sec["name"]}
        for k, d in SECTION_DEFAULTS.items():
            v = sec.get(k, d)
            if v != d and v is not None:
                s[k] = v
        s["chords"] = format_bars(sec.get("bars", []))
        out["sections"].append(s)
    arr = [a["section"] + (" x%d" % a["repeat"] if a.get("repeat") else "") for a in song.get("arrangement") or []]
    if arr:
        out["arrangement"] = arr
    return out


def format_bars(bars, per_line=4):
    lines = []
    for i in range(0, len(bars), per_line):
        lines.append("| " + " | ".join(bars[i:i + per_line]) + " |")
    return "\n".join(lines)


class _Dumper(yaml.SafeDumper):
    pass


def _str(dumper, value):
    if "\n" in value:
        return dumper.represent_scalar("tag:yaml.org,2002:str", value + "\n", style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", value)


_Dumper.add_representer(str, _str)


def header_comments(text):
    """Righe di commento in testa a un file YAML (conservate quando l'editor lo risalva)."""
    lines = []
    for line in text.splitlines():
        if line.startswith("#"):
            lines.append(line)
        elif line.strip():
            break
    return lines


def to_yaml(song):
    text = yaml.dump(to_song_dict(song), Dumper=_Dumper, sort_keys=False, allow_unicode=True,
                     default_flow_style=False, width=120)
    header = song.get("header") or ["# Creato con backingtrack"]
    return "\n".join(header) + "\n" + text


def groove_label(name):
    return "%s — %s" % (name, GROOVES[name]["desc"].split(":", 1)[-1].strip())
