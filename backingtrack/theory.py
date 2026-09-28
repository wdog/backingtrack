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
