"""Accordi: parsing dei simboli e voicing chitarristici."""
import re

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
            raise SongError("accordo non riconosciuto: '%s'" % token)
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
