"""Accordi: parsing dei simboli e voicing chitarristici."""
import re

from .i18n import _
from .errors import SongError

NOTE_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
CHORD_RE = re.compile(r"^([A-G])([#b]?)([^/]*)(?:/([A-G][#b]?))?$")

# suffisso -> (terza, quinta, settima/sesta, estensione) in semitoni dalla tonica
QUALITIES = {}
for _names, _q in [
    (["", "M", "maj"], (4, 7, None, None)),
    (["m", "min", "-"], (3, 7, None, None)),
    (["7", "dom7"], (4, 7, 10, None)),
    (["maj7", "M7", "Δ", "Δ7"], (4, 7, 11, None)),
    (["m7", "min7", "-7"], (3, 7, 10, None)),
    (["mmaj7", "m(maj7)"], (3, 7, 11, None)),
    (["6"], (4, 7, 9, None)),
    (["m6", "-6"], (3, 7, 9, None)),
    (["9"], (4, 7, 10, 14)),
    (["maj9", "M9"], (4, 7, 11, 14)),
    (["m9", "-9"], (3, 7, 10, 14)),
    (["add9"], (4, 7, None, 14)),
    (["13"], (4, 7, 10, 21)),
    (["7#9"], (4, 7, 10, 15)),
    (["7b9"], (4, 7, 10, 13)),
    (["sus4", "sus"], (5, 7, None, None)),
    (["sus2"], (2, 7, None, None)),
    (["7sus4", "7sus"], (5, 7, 10, None)),
    (["dim", "°"], (3, 6, None, None)),
    (["dim7", "°7"], (3, 6, 9, None)),
    (["m7b5", "ø", "ø7"], (3, 6, 10, None)),
    (["aug", "+"], (4, 8, None, None)),
    (["7#5", "aug7", "+7"], (4, 8, 10, None)),
    (["5"], (None, 7, None, None)),
]:
    for _n in _names:
        QUALITIES[_n] = _q


OPEN_STRINGS = [40, 45, 50, 55, 59, 64]  # corde 6..1: MI LA RE SOL SI mi

# Scale per la tastiera della GUI: intervalli dalla tonica, nota caratteristica (blue note nei blues, la nota che
# distingue il modo negli altri; None = nessuna), minor = box CAGED con forme minori (scale con la terza minore)
SCALES = {
    "Pentatonica minore": dict(steps=(0, 3, 5, 7, 10), blue=None, minor=True),
    "Pentatonica maggiore": dict(steps=(0, 2, 4, 7, 9), blue=None, minor=False),
    "Blues minore": dict(steps=(0, 3, 5, 6, 7, 10), blue=6, minor=True),
    "Blues maggiore": dict(steps=(0, 2, 3, 4, 7, 9), blue=3, minor=False),
    "Maggiore (ionica)": dict(steps=(0, 2, 4, 5, 7, 9, 11), blue=None, minor=False),
    "Minore naturale (eolia)": dict(steps=(0, 2, 3, 5, 7, 8, 10), blue=None, minor=True),
    "Dorica": dict(steps=(0, 2, 3, 5, 7, 9, 10), blue=9, minor=True),
    "Misolidia": dict(steps=(0, 2, 4, 5, 7, 9, 10), blue=10, minor=False),
    "Lidia": dict(steps=(0, 2, 4, 6, 7, 9, 11), blue=6, minor=False),
    "Frigia": dict(steps=(0, 1, 3, 5, 7, 8, 10), blue=1, minor=True),
    "Minore armonica": dict(steps=(0, 2, 3, 5, 7, 8, 11), blue=11, minor=True),
    "Minore melodica": dict(steps=(0, 2, 3, 5, 7, 9, 11), blue=11, minor=True),
    # box di B.B. King: 1 2 b3 4 5 6 in una posizione sola; la b3 (rosa) è quella da tirare verso la 3
    "B.B. King box": dict(steps=(0, 2, 3, 5, 7, 9), blue=3, minor=False, shapes="BB"),
    # box di Albert King: 1 b3 4 5 b7 in cima al 2° box della pentatonica minore, fatto per le tirate
    "Albert King box": dict(steps=(0, 3, 5, 7, 10), blue=3, minor=True, shapes="AK"),
}
# forme fisse: (nome, corda della tonica, [(corda, intervallo)]); corde 1 = mi cantino ... 6 = MI grave
SHAPES = {
    "BB": (("BB", 2, ((1, 5), (1, 7), (2, 0), (2, 2), (2, 3), (3, 9))),          # classico: tonica sulla 2a
           ("BB giù", 3, ((2, 5), (2, 7), (3, 0), (3, 2), (3, 3), (4, 9)))),    # stesso box una corda sotto
    "AK": (("AK", 2, ((3, 7), (2, 10), (2, 0), (1, 3), (1, 5))),                 # in A: tasti 8-10
           ("AK giù", 3, ((4, 7), (3, 10), (3, 0), (2, 3), (2, 5)))),
}
DEGREES = {0: "1", 1: "b2", 2: "2", 3: "b3", 4: "3", 5: "4", 6: "b5", 7: "5", 8: "b6", 9: "6", 10: "b7", 11: "7"}
SHARP_FOUR = {"Lidia"}  # qui l'intervallo 6 è una quarta aumentata (#4), non la b5 del blues


def degree(scale, iv):
    return "#4" if iv == 6 and scale in SHARP_FOUR else DEGREES[iv]


# box CAGED: (forma, primo, ultimo tasto) rispetto alla tonica sulla 6a corda, in ordine lungo il manico.
# Le forme minori (Em, Dm, Cm, Am, Gm) cadono sugli stessi box di quelle maggiori della relativa maggiore.
CAGED_MAJOR = (("E", -1, 2), ("D", 1, 5), ("C", 4, 7), ("A", 6, 9), ("G", 9, 12))
CAGED_MINOR = (("E", 0, 3), ("D", 2, 5), ("C", 4, 8), ("A", 7, 10), ("G", 9, 12))
KEY_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
MINOR_KEY_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]  # C# minore, non Db minore


def scale_names(root, scale):
    """Nomi delle note della scala: ogni grado ha la sua lettera (b5 di A = Eb, #4 di A = D#)."""
    info = SCALES[scale]
    root_name = (MINOR_KEY_NAMES if info["minor"] else KEY_NAMES)[root]
    letters = "CDEFGAB"
    first = letters.index(root_name[0])
    names = {}
    for st in info["steps"]:
        n = int(degree(scale, st).lstrip("b#"))
        letter = letters[(first + n - 1) % 7]
        diff = (root + st - NOTE_PC[letter]) % 12
        names[(root + st) % 12] = letter + {0: "", 1: "#", 2: "##", 11: "b", 10: "bb"}[diff]
    return names


def shape_notes(root, scale, frets=15):
    """Scale a forma fissa: [(nome forma, [(corda, tasto, intervallo)])] per ogni posizione sul manico."""
    out = []
    for name, root_string, notes in SHAPES[SCALES[scale]["shapes"]]:
        open_root = OPEN_STRINGS[6 - root_string]
        for rf in range(frets + 1):
            if (open_root + rf) % 12 != root:
                continue
            placed = []
            for string, iv in notes:
                op = OPEN_STRINGS[6 - string]
                # tasto con quell'intervallo più vicino alla tonica (la mano resta in posizione)
                f = min((f for f in range(rf - 4, rf + 5) if (op + f - root) % 12 == iv), key=lambda f: abs(f - rf))
                placed.append((string, f, iv))
            if all(0 <= f <= frets for _s, f, _iv in placed):
                out.append((name, placed))
    return out


def caged_boxes(root, scale, frets=15):
    """Box CAGED visibili tra il tasto 0 e 'frets': [(forma, primo, ultimo)] ordinati lungo il manico.

    Per le scale a forma fissa (B.B. King box) ritorna le posizioni di quelle forme.
    """
    if SCALES[scale].get("shapes"):
        return sorted(((n, min(f for _s, f, _i in ps), max(f for _s, f, _i in ps))
                       for n, ps in shape_notes(root, scale, frets)), key=lambda x: x[1])
    shapes = CAGED_MINOR if SCALES[scale]["minor"] else CAGED_MAJOR
    r6 = (root - OPEN_STRINGS[0]) % 12
    boxes = []
    for k in (-12, 0, 12):
        for shape, lo, hi in shapes:
            a, b = r6 + lo + k, r6 + hi + k
            if a >= -1 and b <= frets + 1:
                boxes.append((shape, max(a, 0), min(b, frets)))
    return sorted(boxes, key=lambda x: x[1])


CAGED = "CAGED"  # ordine dei box salendo lungo il manico (ciclico: dopo D torna C)


def toggle_box(selected, shape):
    """Selezione di box adiacenti (stringa in ordine CAGED ciclico, "" = tutti): clic su 'shape'.

    Box accanto alla selezione = si aggiunge; box a un'estremità = si toglie; altrimenti resta solo lui.
    """
    if not selected:
        return shape
    i = CAGED.index(shape)
    start = next(j for j in range(5) if CAGED[j] in selected and CAGED[j - 1] not in selected) \
        if len(selected) < 5 else i
    arc = "".join(CAGED[(start + k) % 5] for k in range(len(selected)))  # selezione in ordine lungo il manico
    if shape in arc:
        if len(arc) == 1:
            return ""
        return arc[1:] if shape == arc[0] else arc[:-1] if shape == arc[-1] else shape
    if CAGED[(i + 1) % 5] == arc[0]:
        return shape + arc
    if CAGED[i - 1] == arc[-1]:
        return arc + shape
    return shape


def suggest_scales(tokens):
    """Scale adatte a una sezione, dagli accordi: [(tonica, scala, motivo)], la migliore per prima.

    La tonalità è quella del primo accordo (di solito il I). Prima i casi tipici (blues, vamp modali),
    poi la tonalità maggiore che contiene tutti gli accordi.
    """
    # ponytail: tonica = primo accordo; un brano che parte sul IV viene letto male, basta un'analisi delle cadenze
    chords = []
    for t in tokens:
        try:
            chords.append(Chord(t))
        except SongError:
            pass
    if not chords:
        return []

    def kind(c):
        if c.third is None:
            return "5"
        if c.third == 3:
            return "dim" if c.fifth == 6 else "min"
        return "dom" if c.seventh == 10 else "maj"
    tonic = chords[0].root
    rel = {((c.root - tonic) % 12, kind(c)) for c in chords}
    ivs = {iv for iv, _k in rel}
    k0 = kind(chords[0])
    has = lambda iv, *kinds: any(i == iv and k in kinds for i, k in rel)
    out = []

    def add(names, why, root=tonic):
        for n in names:
            if (root, n) not in [(r, s) for r, s, _w in out]:
                out.append((root, n, why))

    if ivs <= {0, 5, 7} and any(k == "dom" for _i, k in rel) and all(k in ("dom", "maj", "5") for _i, k in rel):
        add(["Blues minore", "Blues maggiore", "Misolidia", "B.B. King box", "Albert King box"], _("blues: I7 IV7 V7"))
    if k0 == "min" and has(5, "dom"):
        add(["Dorica", "Pentatonica minore", "Blues minore"], _("vamp dorico: i7 e IV7"))
    if k0 == "min" and has(1, "maj"):
        add(["Frigia"], _("vamp frigio: i e bII"))
    if k0 in ("maj", "dom") and has(10, "maj", "dom"):
        add(["Misolidia", "Pentatonica maggiore", "Blues maggiore"], _("rock modale: I e bVII"))
    if k0 in ("maj", "dom") and has(2, "maj"):
        add(["Lidia"], _("vamp lidio: I e II maggiore"))
    if k0 == "min" and has(7, "dom") and not has(5, "dom"):
        add(["Minore armonica", "Pentatonica minore"], _("minore col V7"))
    if k0 == "min" and ivs <= {0, 3, 5, 7, 8, 10}:
        add(["Blues minore", "Pentatonica minore", "Minore naturale (eolia)"], _("giro minore"))
    # ripiego: la tonalità maggiore che contiene più accordi (triadi diatoniche; una settima su un grado della scala
    # conta anche se non è diatonica: è una dominante secondaria, es. D7 in C). Basta che ne contenga i 2/3.
    diatonic = {0: "maj", 2: "min", 4: "min", 5: "maj", 7: "maj", 9: "min", 11: "dim"}

    def fits(c, key):
        iv = (c.root - key) % 12
        return iv in diatonic and (kind(c) in (diatonic[iv], "5", "dom") or (kind(c) == "dim" and iv == 2))
    if not out:
        score = lambda key: (sum(fits(c, key) for c in chords), (tonic - key) % 12 in (0, 9))
        key = max(range(12), key=lambda k: (score(k), -((k - tonic) % 12)))
        if score(key)[0] * 3 >= len(chords) * 2:
            if (tonic - key) % 12 == 9 or k0 == "min":
                add(["Minore naturale (eolia)", "Pentatonica minore", "Blues minore"], _("accordi della scala minore"))
            else:
                add(["Maggiore (ionica)", "Pentatonica maggiore", "Blues maggiore"], _("accordi della scala maggiore"),
                    root=key)
    return out[:5]


def fretboard_notes(root, scale, frets=15):
    """Note della scala sul manico: [(corda 6..1, tasto, intervallo dalla tonica)]."""
    if SCALES[scale].get("shapes"):  # solo le note delle forme, non tutto il manico
        return sorted({n for _name, ps in shape_notes(root, scale, frets) for n in ps})
    steps = set(SCALES[scale]["steps"])
    return [(6 - i, f, (op + f - root) % 12) for i, op in enumerate(OPEN_STRINGS)
            for f in range(frets + 1) if (op + f - root) % 12 in steps]

# forme aperte (tasti corda 6..1, x = muta), cercate per (tonica, qualità, basso) dopo la trasposizione
OPEN_SHAPES = {
    "C": "x32010", "A": "x02220", "G": "320003", "E": "022100", "D": "xx0232",
    "Am": "x02210", "Em": "022000", "Dm": "xx0231",
    "E7": "020100", "A7": "x02020", "D7": "xx0212", "G7": "320001", "C7": "x32310", "B7": "x21202",
    "Cmaj7": "x32000", "Fmaj7": "xx3210", "Amaj7": "x02120", "Dmaj7": "xx0222", "Gmaj7": "320002",
    "Am7": "x02010", "Em7": "020000", "Dm7": "xx0211",
    "Asus4": "x02230", "Dsus4": "xx0233", "Esus4": "022200", "Asus2": "x02200", "Dsus2": "xx0230",
    "Cadd9": "x32030", "A6": "x02222", "E6": "022120", "C6": "x32210", "G6": "320000",
    "G/B": "x20003", "C/G": "332010", "D/F#": "2x0232", "C/E": "032010", "Am/G": "302210",
}


class Chord:
    """Accordo con voicing a corde: ogni metodo ritorna [(pitch, corda)] dal grave all'acuto.

    Corde numerate come sulla chitarra: 6 = MI grave, 1 = mi cantino.
    """

    def __init__(self, token, transpose=0):
        m = CHORD_RE.match(token)
        if not m or m.group(3) not in QUALITIES:
            raise SongError(_("accordo non riconosciuto: '%s'") % token)
        letter, acc, qual, bass = m.groups()
        self.root = (NOTE_PC[letter] + {"#": 1, "b": -1, "": 0}[acc] + transpose) % 12
        self.bass = self.root
        if bass:
            b = NOTE_PC[bass[0]] + {"#": 1, "b": -1}.get(bass[1:], 0)
            self.bass = (b + transpose) % 12
        self.third, self.fifth, self.seventh, self.ext = QUALITIES[qual]
        names = FLAT_NAMES if acc == "b" else SHARP_NAMES
        self.name = names[self.root] + qual + ("/" + names[self.bass] if bass else "")

    def low_root(self):
        """Tonica sulla corda di MI (E2..G#2) o di LA (A2..D#3)."""
        return 40 + (self.root - 40) % 12

    def root_string(self):
        return 6 if self.low_root() < 45 else 5

    def _strung(self, pitches):
        rs = self.root_string()
        return [(p, max(1, rs - i)) for i, p in enumerate(pitches)]

    def full(self):
        """Voicing tipo barré: forma di MI (6 corde) o di LA (5 corde)."""
        r = self.low_root()
        if self.third is None:
            return self._strung([r, r + 7, r + 12])
        slots = [0, self.fifth, self.seventh if self.seventh is not None else 12,
                 self.third + 12, self.fifth + 12, 24]
        if self.ext == 21:
            slots[4] = 21
        elif self.ext is not None:
            slots[5] = self.ext + 12
        if r >= 45:  # forma di LA: 5 corde
            if self.ext is not None and self.ext != 21:
                slots[4] = slots[5]
            slots.pop()
        notes = [r + s for s in slots]
        if self.bass != self.root:
            b = r - (self.root - self.bass) % 12
            b = b if b >= 36 else b + 12
            if self.root_string() == 5 and b < r:  # basso sulla corda di MI grave
                return [(b, 6)] + self._strung(sorted(set(r + s for s in slots)))
            notes[0] = b
        return self._strung(sorted(set(notes)))

    def top(self, n=4):
        return self.full()[-n:]

    def jazz(self):
        """Voicing jazz a 4 note su corde non adiacenti: tonica, settima (o sesta/ottava), terza, quinta
        o estensione (9, 13). Tonica sulla 6a: corde 6-4-3-2; sulla 5a: corde 5-3-2-1."""
        r, rs = self.low_root(), self.root_string()
        if self.third is None:
            return self.power()
        seventh = self.seventh if self.seventh is not None else (9 if self.third == 4 else 12)
        top = self.fifth + 12
        if self.ext == 21:
            top = 21
        elif self.ext is not None:
            top = self.ext + 12 if self.ext + 12 > self.third + 12 else self.ext + 24
        notes = [r, r + seventh, r + self.third + 12, r + top]
        strings = [rs, rs - 2, rs - 3, rs - 4]
        if self.bass != self.root:  # slash: il basso al posto della tonica
            b = r - (self.root - self.bass) % 12
            notes[0] = b if b >= 40 else b + 12
        return list(zip(notes, strings))

    def _key(self):
        return self.root, (self.third, self.fifth, self.seventh, self.ext), self.bass

    def open(self):
        """Forma aperta in prima posizione (C x32010, G 320003…), o None se l'accordo non ne ha una."""
        shape = _OPEN_BY_KEY.get(self._key())
        if shape is None:
            return None
        return [(OPEN_STRINGS[i] + int(f), 6 - i) for i, f in enumerate(shape) if f != "x"]

    def triad(self):
        """Triade stretta sulle corde 3-2-1, nella posizione più vicina al do centrale."""
        tones = {(self.root + iv) % 12 for iv in (0, self.third if self.third is not None else 7, self.fifth)}
        best = None
        for low in range(55, 67):
            if low % 12 not in tones:
                continue
            notes = [low]
            while len(notes) < 3:
                n = notes[-1] + 1
                while n % 12 not in tones or n % 12 in {x % 12 for x in notes}:
                    n += 1
                notes.append(n)
            if notes[2] <= 76 and (best is None or abs(notes[0] - 60) < abs(best[0] - 60)):
                best = notes
        return list(zip(best, (3, 2, 1)))

    def voicing(self, kind="barre"):
        """Accordo pieno nel voicing scelto: barre | open | jazz | triad (open ripiega sul barré)."""
        if kind == "open":
            return self.open() or self.full()
        if kind == "jazz":
            return self.jazz()
        if kind == "triad":
            return self.triad()
        return self.full()

    def power(self):
        r = self.low_root()
        return self._strung([r, r + (self.fifth or 7), r + 12])

    def bass_note(self, which="R"):
        r, rs = self.low_root(), self.root_string()
        if which == "5":
            return [(r + 7, rs - 1)] if r + 7 <= 52 else [(r - 5, rs + 1)]
        return [(r, rs)]

    def dyad(self, interval):
        r, rs = self.low_root(), self.root_string()
        return [(r, rs), (r + interval, rs - 1)]


VOICINGS = ("barre", "open", "jazz", "triad")
_OPEN_BY_KEY = {Chord(name)._key(): shape for name, shape in OPEN_SHAPES.items()}
