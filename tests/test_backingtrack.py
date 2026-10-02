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
from backingtrack.sfz import Instrument, note_number, pitch_offset_cents, read_wav
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

    def test_voicings(self):
        self.assertEqual([p for p, _ in Chord("C").open()], [48, 52, 55, 60, 64])  # x32010
        self.assertEqual([p for p, _ in Chord("A", -2).open()], [43, 47, 50, 55, 59, 67])  # G aperto
        self.assertIsNone(Chord("Bb").open())
        self.assertEqual(Chord("Bb").voicing("open"), Chord("Bb").full())
        for sym in ("C", "F#m", "Bb7", "Ebmaj7", "Am7b5"):
            c = Chord(sym)
            tri = c.triad()
            self.assertEqual([s for _, s in tri], [3, 2, 1])
            self.assertTrue(all(55 <= p <= 76 for p, _ in tri))
            self.assertEqual(len({s for _, s in c.jazz()}), 4)
            for kind in ("barre", "open", "jazz", "triad"):
                strings = [s for _, s in c.voicing(kind)]
                self.assertEqual(len(strings), len(set(strings)), (sym, kind))

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

    @staticmethod
    def _pluck(freq, sr=44100, secs=1.2):
        """Nota pizzicata sintetica: armoniche che decadono."""
        t = np.arange(int(sr * secs)) / sr
        return sum(np.sin(2 * np.pi * freq * h * t) / h for h in range(1, 6)) * np.exp(-t * 2)

    def test_pitch_offset(self):
        a2 = 110.0
        for cents in (-30, 0, 12, 25):
            x = self._pluck(a2 * 2 ** (cents / 1200))
            self.assertAlmostEqual(pitch_offset_cents(x[None, :], 44100, 45), cents, delta=1.5)
        self.assertIsNone(pitch_offset_cents(self._pluck(a2 * 2 ** (70 / 1200))[None, :], 44100, 45))
        noise = np.random.default_rng(1).standard_normal(44100)
        self.assertIsNone(pitch_offset_cents(noise[None, :], 44100, 45))

    def test_autotune_correction(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self._wav(d / "a.wav", (self._pluck(110 * 2 ** (20 / 1200)) * 0.5)[None, :].astype(np.float32))
            (d / "i.sfz").write_text("<region> sample=a.wav key=45\n")
            ins = Instrument(d / "i.sfz", autotune=True)
            r = ins.regions[0]
            self.assertAlmostEqual(ins.tune_correction(r), -0.20, delta=0.015)
            ins.save_tuning()
            again = Instrument(d / "i.sfz", autotune=True)  # la misura resta in cache
            self.assertTrue((d / ".backingtrack-tuning.json").is_file())
            self.assertAlmostEqual(again.tune_correction(again.regions[0]), ins.tune_correction(r))
            self.assertEqual(Instrument(d / "i.sfz").tune_correction(r), 0.0)


if __name__ == "__main__":
    unittest.main()


class TestSongfile(unittest.TestCase):
    # i messaggi controllati qui sono quelli italiani (la lingua predefinita è l'inglese)
    def setUp(self):
        from backingtrack import i18n
        i18n.set_lang("it")

    def tearDown(self):
        from backingtrack import i18n
        i18n.set_lang(None)

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


class TestScales(unittest.TestCase):
    def test_blues_scales_and_caged(self):
        from backingtrack import theory
        self.assertEqual(sorted(theory.scale_names(9, "Blues minore").values()), sorted("A C D Eb E G".split()))
        self.assertEqual(sorted(theory.scale_names(7, "Blues maggiore").values()), sorted("G A Bb B D E".split()))
        # A minore: box Em ai tasti 5-8 (il "box 1"), G maggiore: forma E ai tasti 2-5
        self.assertIn(("E", 5, 8), theory.caged_boxes(9, "Blues minore"))
        self.assertIn(("E", 2, 5), theory.caged_boxes(7, "Blues maggiore"))
        notes = theory.fretboard_notes(9, "Blues minore")
        self.assertIn((6, 5, 0), notes)   # A sulla 6a corda, 5o tasto = tonica
        self.assertIn((5, 6, 6), notes)   # Eb sulla 5a corda, 6o tasto = b5
        self.assertTrue(all(iv in theory.DEGREES for _s, _f, iv in notes))

    def test_spelling_and_box_selection(self):
        from backingtrack import theory

        def spelled(root, scale):
            names = theory.scale_names(root, scale)
            return [names[(root + st) % 12] for st in theory.SCALES[scale]["steps"]]
        self.assertEqual(spelled(9, "Dorica"), "A B C D E F# G".split())
        self.assertEqual(spelled(9, "Lidia"), "A B C# D# E F# G#".split())
        self.assertEqual(spelled(4, "Minore armonica"), "E F# G A B C D#".split())
        t = theory.toggle_box
        self.assertEqual(t("", "E"), "E")
        self.assertEqual(t("E", "D"), "ED")       # adiacente sopra: si aggiunge
        self.assertEqual(t("ED", "G"), "GED")     # adiacente sotto
        self.assertEqual(t("GED", "G"), "ED")     # estremità: si toglie
        self.assertEqual(t("GED", "E"), "E")      # in mezzo: resta solo lui
        self.assertEqual(t("ED", "A"), "A")       # non adiacente: ricomincia
        self.assertEqual(t("DC", "A"), "DCA")     # ciclico: dopo D viene C
        self.assertEqual(t("E", "E"), "")         # tolto l'ultimo = tutti

    def test_blues_boxes_and_suggestions(self):
        from backingtrack import theory
        bb = dict(theory.shape_notes(9, "B.B. King box"))["BB"]
        self.assertIn((2, 10, 0), bb)   # A: tonica sulla 2a corda, 10° tasto
        self.assertIn((3, 11, 9), bb)   # la 6 (F#) sulla 3a corda, un tasto sopra
        ak = dict(theory.shape_notes(9, "Albert King box"))["AK"]
        self.assertEqual(sorted(f for _s, f, _i in ak), [8, 8, 9, 10, 10])
        sug = lambda t: [(theory.KEY_NAMES[r], s) for r, s, _w in theory.suggest_scales(t.split())]
        self.assertEqual(sug("A7 D7 A7 E7")[0], ("A", "Blues minore"))
        self.assertEqual(sug("Am7 D7")[0], ("A", "Dorica"))
        self.assertEqual(sug("A G D A")[0], ("A", "Misolidia"))
        self.assertEqual(sug("C G Am F")[0], ("C", "Maggiore (ionica)"))
        self.assertEqual(sug("Am Bb")[0], ("A", "Frigia"))
        self.assertEqual(sug(""), [])


class TestTranslations(unittest.TestCase):
    """Ogni testo passato a _() o mostrato dalla GUI deve avere la traduzione inglese, con gli stessi segnaposto."""

    def test_every_text_is_translated(self):
        import ast
        import re
        from backingtrack import songfile, theory
        from backingtrack.grooves import GROOVES
        from backingtrack.locale_en import EN, GROOVES_EN
        texts = set()
        for f in Path("backingtrack").glob("*.py"):
            for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
                if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_" and n.args \
                        and isinstance(n.args[0], ast.Constant):
                    texts.add(n.args[0].value)
        texts |= set(theory.SCALES) | set(songfile.TEMPLATES)
        try:
            from backingtrack import gui
        except ImportError:
            gui = None
        if gui is not None and gui.Gtk is not None:
            for title, _icon, items in gui.HELP:
                texts.add(title)
                for kind, body in items:
                    pairs = body if kind == "code" else [(kind, body)] if kind not in ("p", "h") else [("", body)]
                    for left, right in pairs:
                        texts |= {left, right} - {"", "code"}
            texts |= set(gui.SCALE_DESC.values()) | {gui.SWING_HINT} | {g for g, _n in gui.TEMPLATE_GROUPS}
        placeholders = lambda s: re.findall(r"%[-0-9.]*[sdgf%]", s)
        missing = sorted(t for t in texts if t not in EN and re.search(r"[a-zà-ù]{3}", t)
                         and not re.fullmatch(r"[A-G0-9#b/ .%+·×–NC]*|[A-Za-z]+\+[A-Za-z0-9+ ]*", t))
        self.assertEqual(missing, [])
        for it, en in EN.items():
            self.assertEqual(placeholders(it), placeholders(en), it)
        self.assertEqual(set(GROOVES), set(GROOVES_EN))

    def test_switch_language(self):
        from backingtrack import i18n, songfile
        try:
            i18n.set_lang("en")
            self.assertEqual(songfile.check_bar("%", True)[:3], "'%'")
            self.assertIn("previous", songfile.check_bar("%", True))
            i18n.set_lang("it")
            self.assertIn("precedente", songfile.check_bar("%", True))
        finally:
            i18n.set_lang(None)
