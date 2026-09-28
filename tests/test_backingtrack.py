"""Test senza campioni: python -m unittest discover tests"""
import random
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from backingtrack.arranger import PPQ, Arranger
from backingtrack.errors import SongError
from backingtrack.grooves import GROOVES
from backingtrack.midi import write_midi
from backingtrack.sfz import Instrument, note_number, read_wav
from backingtrack.song import build_timeline, load_song, parse_bars
from backingtrack.theory import Chord

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class TestChords(unittest.TestCase):
    def test_names_and_transpose(self):
        self.assertEqual(Chord("A7").name, "A7")
        self.assertEqual(Chord("Bb", 2).name, "C")
        self.assertEqual(Chord("D/F#").bass, 6)

    def test_voicings_on_strings(self):
        e = Chord("E").full()
        self.assertEqual([p for p, _ in e], [40, 47, 52, 56, 59, 64])
        self.assertEqual([s for _, s in e], [6, 5, 4, 3, 2, 1])
        a = Chord("A").full()
        self.assertEqual(a[0], (45, 5))
        self.assertEqual(len(a), 5)
        self.assertEqual(Chord("E5").power(), [(40, 6), (47, 5), (52, 4)])

    def test_unknown(self):
        with self.assertRaises(SongError):
            Chord("H7")
        with self.assertRaises(SongError):
            Chord("Cxyz")


class TestSong(unittest.TestCase):
    def test_bars(self):
        bars = parse_bars("| C . G . | Am | % | N.C. |", 0, "t")
        self.assertEqual(len(bars), 4)
        self.assertEqual([(s, d) for s, d, _ in bars[0]], [(0, 2), (2, 2)])
        self.assertIs(bars[2], bars[1])
        self.assertIsNone(bars[3][0][2])

    def test_arrangement_and_repeat(self):
        song = {"groove": "blues", "sections": [
            {"name": "A", "repeat": 2, "chords": "| E | A |"},
            {"name": "B", "chords": "| B7 |"}]}
        order, tl = build_timeline(song)
        self.assertEqual(len(tl), 5)
        song["arrangement"] = ["B", "A x3", "B"]
        order, tl = build_timeline(song)
        self.assertEqual([(s["name"], r) for s, r in order], [("B", 1), ("A", 3), ("B", 1)])
        self.assertEqual(len(tl), 8)

    def test_errors(self):
        with self.assertRaises(SongError):
            build_timeline({"sections": [{"name": "A", "chords": "| E |"}], "arrangement": ["Z"]})
        with self.assertRaises(SongError):
            build_timeline({"groove": "polka", "sections": [{"name": "A", "chords": "| E |"}]})

    def test_examples_parse(self):
        files = sorted(EXAMPLES.glob("*/*.yaml"))
        self.assertGreaterEqual(len(files), 60)
        for f in files:
            with self.subTest(f=f.name):
                order, tl = build_timeline(load_song(f))
                self.assertTrue(tl)


class TestArranger(unittest.TestCase):
    def arrange(self, groove, **kw):
        song = dict(tempo=120, groove=groove, sections=[{"name": "A", "chords": "| E | A | B7 | E |"}], **kw)
        return Arranger(song).arrange(build_timeline(song)[1])

    def test_all_grooves(self):
        for g in GROOVES:
            with self.subTest(groove=g):
                arr = self.arrange(g)
                parts = {n.part for n in arr.notes}
                self.assertIn("drums", parts)
                self.assertIn("guitar", parts)
                self.assertEqual("guitar2" in parts, bool(GROOVES[g].get("double")))
                self.assertEqual(arr.length, (1 + 4 + 2) * 4 * PPQ)  # count-in + 4 battute + finale

    def test_strings_do_not_overlap(self):
        arr = self.arrange("rock/strum")
        last = {}
        for n in sorted(arr.notes, key=lambda n: n.start):
            if n.part.startswith("guitar"):
                key = (n.part, n.string)
                if key in last:
                    self.assertLessEqual(last[key], n.start)
                last[key] = n.end

    def test_midi_file(self):
        arr = self.arrange("blues", bass=True)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.mid"
            write_midi(p, arr, "test")
            data = p.read_bytes()
        self.assertEqual(data[:4], b"MThd")
        fmt, ntracks, ppq = struct.unpack(">HHH", data[8:14])
        self.assertEqual((fmt, ntracks, ppq), (1, 4, PPQ))  # tempo, chitarra, basso, batteria


class TestSfz(unittest.TestCase):
    def test_note_number(self):
        self.assertEqual(note_number("c4"), 60)
        self.assertEqual(note_number("e2"), 40)
        self.assertEqual(note_number("f#3"), 54)
        self.assertEqual(note_number("36"), 36)

    def _wav(self, path, data, bits=16):
        ch, n = data.shape
        if bits == 16:
            raw = (data.T * 32767).astype("<i2").tobytes()
            tag = 1
        else:
            raw = data.T.astype("<f4").tobytes()
            tag = 3
        fmt = struct.pack("<HHIIHH", tag, ch, 44100, 44100 * ch * bits // 8, ch * bits // 8, bits)
        body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(raw)) + raw
        Path(path).write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)

    def test_wav_reader(self):
        x = np.linspace(-0.5, 0.5, 100, dtype=np.float32).reshape(1, -1)
        with tempfile.TemporaryDirectory() as d:
            for bits in (16, 32):
                p = Path(d) / ("t%d.wav" % bits)
                self._wav(p, x, bits)
                y, sr = read_wav(p)
                self.assertEqual(sr, 44100)
                self.assertEqual(y.shape, (1, 100))
                self.assertTrue(np.allclose(x, y, atol=1e-3))

    def test_instrument_selection(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "s").mkdir()
            for name in ("lo", "hi", "rr1", "rr2"):
                self._wav(d / "s" / (name + ".wav"), np.zeros((1, 10), dtype=np.float32))
            (d / "i.sfz").write_text(
                "<control> default_path=s\\\n"
                "<group> key=40 <region> sample=lo.wav hivel=64 <region> sample=hi.wav lovel=65\n"
                "<group> lokey=50 hikey=52 pitch_keycenter=51 seq_length=2\n"
                "<region> sample=rr1.wav seq_position=1 <region> sample=rr2.wav seq_position=2\n")
            ins = Instrument(d / "i.sfz")
            rng = random.Random(1)
            self.assertEqual(ins.select(40, 30, rng)[0].sample.name, "lo.wav")
            self.assertEqual(ins.select(40, 100, rng)[0].sample.name, "hi.wav")
            seq = [ins.select(51, 100, rng)[0].sample.name for _ in range(4)]
            self.assertEqual(seq, ["rr1.wav", "rr2.wav", "rr1.wav", "rr2.wav"])
            self.assertEqual(ins.select(52, 100, rng)[0].center, 51)
            self.assertEqual(ins.select(60, 100, rng), [])


if __name__ == "__main__":
    unittest.main()


class TestSongfile(unittest.TestCase):
    def test_describe_bar(self):
        from backingtrack import songfile as sf
        self.assertEqual(sf.describe_bar("Em . D C"), "Em 2 tempi · D 1 · C 1")
        self.assertEqual(sf.describe_bar("C . . G"), "C 3 tempi · G 1")
        self.assertEqual(sf.describe_bar("A7"), "A7 per tutta la battuta")
        self.assertEqual(sf.describe_bar("%"), "ripete la battuta precedente")
        self.assertIsNone(sf.describe_bar(". D"))

    def test_check_bar_messages(self):
        from backingtrack import songfile as sf
        self.assertIsNone(sf.check_bar("C G Am F"))
        self.assertIn("Em . D C", sf.check_bar(". D"))
        self.assertIn("prima", sf.check_bar("%", first=True))
        self.assertIn("maiuscola", sf.check_bar("am"))
        self.assertIn("B7", sf.check_bar("H7"))
        self.assertIn("4 simboli", sf.check_bar("A B C D E"))

    def test_templates(self):
        from backingtrack import songfile as sf
        self.assertEqual(sf.template_bars("12-bar blues (quick change)", "E")[:4], ["E7", "A7", "E7", "E7"])
        self.assertEqual(sf.template_bars("Anni '50 I-vi-IV-V", "Bb"), ["Bb", "Gm", "Eb", "F"])
        for name in sf.TEMPLATES:
            for key in sf.KEYS:
                for bar in sf.template_bars(name, key):
                    self.assertIsNone(sf.check_bar(bar), (name, key, bar))

    def test_yaml_roundtrip_examples(self):
        import yaml
        from backingtrack import songfile as sf
        for f in sorted(EXAMPLES.glob("*/*.yaml")):
            with self.subTest(f=f.name):
                model = sf.from_song_dict(load_song(f))
                self.assertEqual(sf.validate(model), [])
                again = yaml.safe_load(sf.to_yaml(model))
                a, b = build_timeline(load_song(f)), build_timeline(again)
                self.assertEqual(len(a[1]), len(b[1]))
                self.assertEqual([(s["name"], r) for s, r in a[0]], [(s["name"], r) for s, r in b[0]])
