"""Dalla timeline alle note: pennate, basso e batteria con swing, fill e umanizzazione."""
import random
from collections import namedtuple

from .errors import SongError
from .grooves import CRASH, HH, KICK, PEDAL, RIDE, STICK, get_groove
from .song import chord_at
from .theory import VOICINGS, Chord

PPQ = 480

# part: guitar | guitar2 | bass | drums      bus: gruppo di mix (ampli, lato, slapback)
Note = namedtuple("Note", "part start end pitch vel string muted bus")


def guitar_bus(amp, side, slap):
    return "gtr:%s:%s%s" % (amp, side, ":slap" if slap else "")


class Arranger:
    def __init__(self, song, tempo=None, bass=False):
        self.song = song
        self.tempo = float(tempo or song.get("tempo", 120))
        if not 30 <= self.tempo <= 320:
            raise SongError("tempo fuori range (30-320 BPM): %g" % self.tempo)
        self.rng = random.Random(song.get("seed", 1))
        self.humanize = float(song.get("humanize", 1.0))
        self.strum_ms = float(song.get("strum_ms", 14))
        self.bass_on = bass or bool(song.get("bass", False))
        self.notes = []
        self.length = 0  # tick

    # utilità ------------------------------------------------------------------
    def ms_ticks(self, ms):
        return ms / 1000 * self.tempo / 60 * PPQ

    def seconds(self, tick):
        return tick / PPQ * 60 / self.tempo

    def jitter(self, ms):
        return self.ms_ticks(self.rng.uniform(-ms, ms) * self.humanize)

    def vel(self, v, scale=1.0):
        v = v * scale + self.rng.uniform(-6, 6) * self.humanize
        return max(1, min(127, int(v)))

    def add(self, part, start, end, pitch, vel, string=0, muted=False, bus=None):
        start = max(0, int(start))
        self.notes.append(Note(part, start, max(int(end), start + 10), pitch, vel, string, muted, bus or part))

    @staticmethod
    def swing(beat, amount):
        """Sposta gli ottavi in levare: 0 = dritto, 1 = terzina piena."""
        if abs(beat % 1 - 0.5) < 1e-6:
            return beat + amount / 6
        return beat

    # chitarra ---------------------------------------------------------------
    def strum(self, part, bus, kind, chord, t0, t1, vel, mute_len, voicing="barre"):
        muted = kind.endswith("m")
        base = kind[:-1] if muted else kind
        up = False
        if base == "D":
            notes = chord.voicing(voicing)
        elif base == "U":
            notes, up = chord.voicing(voicing)[-4:], True
        elif base == "C":
            notes, muted = chord.voicing(voicing)[-4:], True
        elif base == "P":
            notes = chord.power()
        elif base == "J":
            notes = chord.jazz()
        elif base in ("B", "B5"):
            notes = chord.bass_note("5" if base == "B5" else "R")
        elif base in ("R5", "R6", "R7"):
            notes = chord.dyad({"R5": 7, "R6": 9, "R7": 10}[base])
        else:
            raise SongError("evento chitarra sconosciuto '%s'" % kind)
        t1 = min(t1, t0 + PPQ * mute_len) if muted else t1 - PPQ * 0.02
        # pennata più forte = più veloce
        spread = self.ms_ticks(self.strum_ms * (1.35 - vel / 127 * 0.5) * (0.7 if up else 1.0))
        order = list(reversed(notes)) if up else notes
        j = self.jitter(6)
        for i, (p, string) in enumerate(order):
            s = t0 + j + i * spread * self.rng.uniform(0.8, 1.2)
            # giù: accento sui bassi; su: accento sui cantini
            v = self.vel(vel * (1 - 0.035 * i))
            self.add(part, s, t1, p, v, string, muted, bus)

    # basso ------------------------------------------------------------------
    def bass_bar(self, style, segs, bar_tick, bar_idx, swing, scale):
        if style == "eighths":
            hits = [(i / 2, 0) for i in range(8)]
        elif style == "rootfifth":
            hits = [(0, 0), (1, 7), (2, 0), (3, 7)]
        elif style == "stop":
            hits = [(0, 0)]
        elif style == "slow":
            hits = [(0, 0), (1, 7), (2, 9), (3, 7)]
        elif style == "two":
            hits = [(0, 0), (2, 7)]
        elif style == "octave":
            hits = [(i / 2, 12 * (i % 2)) for i in range(8)]
        elif style == "funk":
            hits = [(0, 0), (0.75, 0), (1.5, 12), (2, 0), (2.5, 7), (3.5, 10)]
        elif style == "reggae":
            hits = [(0, 0), (1.5, 7), (2, 12), (3, 10)]
        elif style == "quarters":
            hits = [(b, 0) for b in range(4)]
        elif style == "dotted":
            hits = [(0, 0), (1.5, 0), (3, 7)]
        elif style == "tumbao":
            hits = [(1.5, 7), (3, 0)]
        else:  # walk: R 3 5 6 | b7 6 5 3
            hits = [(b, None) for b in range(4)]
        for k, (beat, iv) in enumerate(hits):
            c = chord_at(segs, beat)
            if c is None:
                continue
            if iv is None:
                third = c.third if c.third in (3, 4) else 4
                iv = ([0, third, 7, 9] if bar_idx % 2 == 0 else [10, 9, 7, third])[k]
            nxt = hits[k + 1][0] if k + 1 < len(hits) else 4
            t0 = bar_tick + self.swing(beat, swing) * PPQ
            t1 = bar_tick + self.swing(nxt, swing) * PPQ - PPQ * 0.08
            root = 28 + (c.bass - 28) % 12
            self.add("bass", t0 + self.jitter(4), t1, root + iv, self.vel(100 if beat % 1 == 0 else 85, scale))

    # batteria ---------------------------------------------------------------
    def drum_hits(self, hits, bar_tick, swing, scale):
        for beat, n, v in hits:
            t = bar_tick + self.swing(beat, swing) * PPQ + self.jitter(4)
            self.add("drums", t, t + PPQ * 0.25, n, self.vel(v, scale))

    @staticmethod
    def replace_from(hits, extra):
        start = min(b for b, _, _ in extra)
        return [h for h in hits if h[0] < start - 1e-6] + list(extra)

    # canzone ----------------------------------------------------------------
    def arrange(self, timeline):
        song = self.song
        bar_ticks = 4 * PPQ
        tick = 0
        if song.get("count_in", True):
            for b in range(4):
                self.add("drums", b * PPQ, b * PPQ + 100, STICK, 100 if b == 0 else 85)
            tick += bar_ticks

        amp_override = song.get("amp")
        first_chord = None
        last_bus = None
        for bar_idx, bar in enumerate(timeline):
            sec = bar["sec"]
            g = get_groove(sec["groove"])
            swing = float(sec["swing"] if sec["swing"] is not None else song.get("swing", g["swing"]))
            amp = amp_override or g["amp"]
            voicing = song.get("voicing") or g.get("voicing", "barre")
            if voicing not in VOICINGS:
                raise SongError("voicing '%s' sconosciuto (usa %s)" % (voicing, ", ".join(VOICINGS)))
            double = song.get("double", g.get("double", False))
            slap = song.get("slapback", g.get("slap", False))
            takes = [("guitar", guitar_bus(amp, "L", slap)), ("guitar2", guitar_bus(amp, "R", slap))] \
                if double else [("guitar", guitar_bus(amp, "C", slap))]
            last_bus = takes
            segs, scale = bar["segs"], sec["volume"]
            if first_chord is None:
                first_chord = next((c for _, _, c in segs if c), None)

            if sec["guitar"]:
                events = sorted(g["guitar"], key=lambda e: e[0])
                for k, ev in enumerate(events):
                    beat, kind, vel = ev[:3]
                    c = chord_at(segs, beat)
                    if c is None:
                        continue
                    if len(ev) > 3 and ev[3] is not None:
                        end_beat = beat + ev[3]
                    else:
                        end_beat = events[k + 1][0] if k + 1 < len(events) else 4
                    for s, _, _ in segs:  # non suonare oltre un cambio accordo
                        if beat < s < end_beat:
                            end_beat = s
                    t0 = tick + self.swing(beat, swing) * PPQ
                    t1 = tick + self.swing(end_beat, swing) * PPQ
                    for part, bus in takes:
                        self.strum(part, bus, kind, c, t0, t1, vel * scale, g.get("mute_len", 0.28), voicing)

            if self.bass_on:
                self.bass_bar(g.get("bass_style", "eighths"), segs, tick, bar_idx, swing, scale)

            if sec["drums"]:
                hits = list(g["drums"])
                if bar["last"] and sec["fill"]:
                    hits = self.replace_from(hits, g["fill"])
                elif (bar["index"] + 1) % 4 == 0:
                    hits = self.replace_from(hits, g["turn"])
                if bar["first"] and song.get("crash", True):
                    hits = [h for h in hits if not (h[0] == 0 and h[1] in (HH, RIDE, PEDAL))]
                    hits.append((0, CRASH, 110))
                self.drum_hits(hits, tick, swing, scale)

            tick += bar_ticks

        if song.get("ending", True) and first_chord:
            end_tok = song.get("ending_chord")
            c = Chord(str(end_tok), int(song.get("transpose", 0))) if end_tok else first_chord
            for part, bus in last_bus:
                self.strum(part, bus, "D", c, tick, tick + bar_ticks * 1.75, 118, 0)
            self.drum_hits([(0, CRASH, 118), (0, KICK, 118)], tick, 0, 1)
            if self.bass_on:
                self.add("bass", tick, tick + bar_ticks * 1.5, 28 + (c.bass - 28) % 12, 110)
            tick += bar_ticks * 2
        self.length = tick
        self.notes = self._choke(self.notes)
        return self

    @staticmethod
    def _choke(notes):
        """Una corda suona una nota alla volta; il basso è monofonico."""
        by_key = {}
        for n in sorted(notes, key=lambda n: n.start):
            if n.part == "drums":
                key = ("drums", n.pitch, id(n))
            elif n.part == "bass":
                key = ("bass",)
            else:
                key = (n.part, n.string)
            by_key.setdefault(key, []).append(n)
        out = []
        for lst in by_key.values():
            for i in range(len(lst) - 1):
                a, b = lst[i], lst[i + 1]
                if a.end > b.start - 1:
                    lst[i] = a._replace(end=max(a.start + 1, b.start - 1))
            out += lst
        out.sort(key=lambda n: n.start)
        return out
