"""Lettura del file canzone YAML e costruzione della timeline di battute."""
import re
from pathlib import Path

import yaml

from .errors import SongError
from .grooves import get_groove
from .theory import Chord


def load_song(path):
    try:
        song = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        raise SongError("impossibile leggere %s: %s" % (path, e))
    if not isinstance(song, dict):
        raise SongError("il file YAML deve contenere una mappa (title, tempo, sections, ...)")
    return song


def parse_bars(text, transpose, where):
    """'| A7 | D7 . A7 . | % | N.C. |' -> lista di battute [(beat_inizio, durata, Chord|None)]."""
    cells = [c.strip() for c in re.split(r"[|\n]", str(text)) if c.strip()]
    bars, prev = [], None
    for n, cell in enumerate(cells, 1):
        if cell == "%":
            if prev is None:
                raise SongError("%s, battuta %d: '%%' senza battuta precedente" % (where, n))
            bars.append(prev)
            continue
        toks = cell.split()
        step = 4 / len(toks)
        segs = []
        for i, t in enumerate(toks):
            if t in (".", "-", "/"):
                if not segs:
                    raise SongError("%s, battuta %d: '%s' a inizio battuta" % (where, n, t))
                s, d, c = segs[-1]
                segs[-1] = (s, d + step, c)
            elif t.upper() in ("N.C.", "NC"):
                segs.append((i * step, step, None))
            else:
                try:
                    segs.append((i * step, step, Chord(t, transpose)))
                except SongError as e:
                    raise SongError("%s, battuta %d: %s" % (where, n, e)) from None
        bars.append(segs)
        prev = segs
    if not bars:
        raise SongError("%s: nessuna battuta" % where)
    return bars


def chord_at(segs, beat):
    for s, d, c in segs:
        if s - 1e-6 <= beat < s + d - 1e-6:
            return c
    return segs[-1][2]


def build_timeline(song, groove_override=None):
    """Ritorna (ordine [(sezione, ripetizioni)], timeline [battuta])."""
    transpose = int(song.get("transpose", 0))
    default_groove = groove_override or song.get("groove", "rock")
    get_groove(default_groove)
    sections = {}
    for i, sec in enumerate(song.get("sections") or []):
        if not isinstance(sec, dict):
            raise SongError("sezione %d: deve essere una mappa con name e chords" % (i + 1))
        name = str(sec.get("name", "Sezione %d" % (i + 1)))
        if "chords" not in sec:
            raise SongError("sezione '%s': manca 'chords'" % name)
        groove_name = groove_override or sec.get("groove", default_groove)
        get_groove(groove_name)
        sections[name] = dict(
            name=name,
            bars=parse_bars(sec["chords"], transpose, "sezione '%s'" % name),
            repeat=int(sec.get("repeat", 1)),
            groove=groove_name,
            swing=sec.get("swing"),
            volume=float(sec.get("volume", 1.0)),
            fill=sec.get("fill", song.get("fills", True)),
            guitar=sec.get("guitar", True),
            drums=sec.get("drums", True),
        )
    if not sections:
        raise SongError("nessuna sezione definita (chiave 'sections')")

    order = []
    for item in song.get("arrangement") or []:
        m = re.match(r"^(.*?)\s*[x×*]\s*(\d+)$", str(item).strip())
        name, reps = (m.group(1), int(m.group(2))) if m else (str(item).strip(), None)
        if name not in sections:
            raise SongError("arrangement: la sezione '%s' non esiste (%s)" % (name, ", ".join(sections)))
        order.append((sections[name], reps if reps is not None else sections[name]["repeat"]))
    if not order:
        order = [(s, s["repeat"]) for s in sections.values()]

    timeline = []
    for sec, reps in order:
        for _rep in range(reps):
            for i, segs in enumerate(sec["bars"]):
                timeline.append(dict(sec=sec, segs=segs, index=i,
                                     first=i == 0, last=i == len(sec["bars"]) - 1))
    return order, timeline
