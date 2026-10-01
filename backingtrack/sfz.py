"""Lettore SFZ minimale: il sottoinsieme di opcode usato dai pacchetti supportati.

Supporta: <control>/<global>/<master>/<group>/<region>, #define/#include, default_path,
key/lokey/hikey/pitch_keycenter (numeri o nomi), lovel/hivel, lorand/hirand, seq_length/seq_position,
locc/hicc, trigger, volume/group_volume, amp_veltrack, amp_velcurve_N, tune/transpose,
offset/end, ampeg_release, group/off_by/off_mode, loop_mode.

Intonazione automatica (strumenti intonati): ogni campione viene misurato una volta e corretto
di quanto è calante/crescente rispetto al suo pitch_keycenter; le misure restano in un JSON accanto all'SFZ.
"""
import json
import re
import struct
from pathlib import Path

import numpy as np

from .i18n import _
from .errors import SongError

NOTE_NAMES = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def note_number(v):
    v = str(v).strip()
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    m = re.fullmatch(r"([a-gA-G])([#b]?)(-?\d)", v)
    if not m:
        raise ValueError(v)
    return (int(m.group(3)) + 1) * 12 + NOTE_NAMES[m.group(1).lower()] + {"#": 1, "b": -1, "": 0}[m.group(2)]


def _read_text(path, defines, root, depth=0):
    if depth > 16:
        raise SongError(_("SFZ: troppi #include annidati"))
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    out = []
    for line in text.splitlines():
        line = line.split("//", 1)[0]
        for m in re.finditer(r'#define\s+(\$\w+)\s+(\S+)', line):
            defines[m.group(1)] = m.group(2)
        line = re.sub(r'#define\s+\$\w+\s+\S+', "", line)
        for k in sorted(defines, key=len, reverse=True):
            line = line.replace(k, defines[k])
        parts = re.split(r'#include\s+"([^"]+)"', line)
        for i, part in enumerate(parts):
            if i % 2:
                rel = part.replace("\\", "/")
                inc = Path(root) / rel  # come da specifica: relativo all'SFZ principale
                if not inc.is_file():
                    inc = Path(path).parent / rel
                out.append(_read_text(inc, defines, root, depth + 1))
            else:
                out.append(part)
        out.append("\n")
    return "".join(out)


def parse(path):
    """Ritorna (control, [opcode della region, già uniti a global/master/group])."""
    text = _read_text(path, {}, Path(path).parent)
    control, scopes, regions = {}, {"global": {}, "master": {}, "group": {}}, []
    target = None
    for chunk in re.split(r"(<\w+>)", text):
        m = re.fullmatch(r"<(\w+)>", chunk)
        if m:
            level = m.group(1)
            if level == "region":
                target = {}
                inherited = {}
                for lvl in ("global", "master", "group"):
                    inherited.update(scopes[lvl])
                regions.append((inherited, target))
            elif level in scopes:
                for lower in ("global", "master", "group")[("global", "master", "group").index(level):]:
                    scopes[lower] = {}
                target = scopes[level]
            elif level == "control":
                target = control
            else:
                target = {}  # <curve>, <effect>, ...: ignorati
            continue
        if target is None:
            continue
        keys = list(re.finditer(r"([A-Za-z0-9_]+)=", chunk))
        for i, km in enumerate(keys):
            end = keys[i + 1].start() if i + 1 < len(keys) else len(chunk)
            target[km.group(1)] = chunk[km.end():end].strip()
    return control, [dict(inh, **own) for inh, own in regions]


class Region:
    def __init__(self, ops, base_dir, default_path, index):
        g = ops.get
        if "key" in ops:
            k = note_number(ops["key"])
            self.lokey = self.hikey = self.center = k
        else:
            self.lokey = note_number(g("lokey", 0))
            self.hikey = note_number(g("hikey", 127))
            self.center = note_number(g("pitch_keycenter", self.lokey))
        if "pitch_keycenter" in ops:
            self.center = note_number(ops["pitch_keycenter"])
        self.lovel, self.hivel = int(g("lovel", 1)), int(g("hivel", 127))
        self.lorand, self.hirand = float(g("lorand", 0)), float(g("hirand", 1))
        self.seq_length, self.seq_position = int(g("seq_length", 1)), int(g("seq_position", 1))
        self.trigger = g("trigger", "attack")
        self.cc = {}
        for k, v in ops.items():
            m = re.fullmatch(r"(lo|hi)cc(\d+)", k)
            if m:
                lo, hi = self.cc.get(int(m.group(2)), (0, 127))
                self.cc[int(m.group(2))] = (int(v), hi) if m.group(1) == "lo" else (lo, int(v))
        self.volume = float(g("volume", 0)) + float(g("group_volume", 0))
        self.veltrack = float(g("amp_veltrack", 100)) / 100
        curve = sorted((int(k[13:]), float(v)) for k, v in ops.items() if k.startswith("amp_velcurve_"))
        self.velcurve = ([(0, 0.0)] + curve + ([(127, 1.0)] if not curve or curve[-1][0] < 127 else [])) \
            if curve else None
        self.tune = float(g("tune", 0)) / 100 + float(g("transpose", 0))
        self.offset, self.end = int(g("offset", 0)), (int(g("end")) if "end" in ops else None)
        self.release = float(g("ampeg_release", 0.03))
        self.group, self.off_by = int(g("group", 0)), int(g("off_by", 0))
        self.off_mode = g("off_mode", "fast")
        self.one_shot = g("loop_mode", "") == "one_shot"
        self.index = index
        sample = (default_path + g("sample", "")).replace("\\", "/")
        self.sample = base_dir / sample

    def vel_gain(self, vel):
        if self.velcurve:
            xs, ys = zip(*self.velcurve)
            return float(np.interp(vel, xs, ys))
        return (1 - self.veltrack) + self.veltrack * (vel / 127) ** 2


def read_wav(path):
    """WAV PCM 8/16/24/32 bit o float 32/64 -> (float32 [canali, campioni], samplerate)."""
    with open(path, "rb") as f:
        buf = f.read()
    if buf[:4] != b"RIFF" or buf[8:12] != b"WAVE":
        raise ValueError(_("non è un file WAV"))
    pos, fmt, data = 12, None, None
    while pos + 8 <= len(buf):
        cid, size = buf[pos:pos + 4], struct.unpack("<I", buf[pos + 4:pos + 8])[0]
        body = buf[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            tag, ch, sr = struct.unpack("<HHI", body[:8])
            bits = struct.unpack("<H", body[14:16])[0]
            if tag == 0xFFFE and len(body) >= 26:  # WAVE_FORMAT_EXTENSIBLE
                tag = struct.unpack("<H", body[24:26])[0]
            fmt = (tag, ch, sr, bits)
        elif cid == b"data":
            data = body
        pos += 8 + size + (size & 1)
    if fmt is None or data is None:
        raise ValueError(_("WAV senza fmt/data"))
    tag, ch, sr, bits = fmt
    width = bits // 8
    data = data[: len(data) - len(data) % (width * ch)]
    if tag == 3:
        x = np.frombuffer(data, "<f4" if bits == 32 else "<f8").astype(np.float32)
    elif width == 2:
        x = np.frombuffer(data, "<i2").astype(np.float32) / 32768
    elif width == 3:
        b = np.frombuffer(data, np.uint8).reshape(-1, 3).astype(np.int32)
        i32 = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        x = (np.where(i32 & 0x800000, i32 - 0x1000000, i32)).astype(np.float32) / 8388608
    elif width == 4:
        x = np.frombuffer(data, "<i4").astype(np.float32) / 2147483648
    else:
        x = (np.frombuffer(data, np.uint8).astype(np.float32) - 128) / 128
    return x.reshape(-1, ch).T.copy(), sr


def pitch_offset_cents(data, sr, key, max_cents=50):
    """Scarto in cent della parte stabile del campione rispetto alla nota `key`; None se non misurabile.

    Autocorrelazione nella finestra dopo l'attacco, cercando il periodo solo entro ±1 semitono
    da quello atteso (niente errori d'ottava). Scarti oltre max_cents non sono stonature ma altro: ignorati.
    """
    x = data.mean(axis=0) if data.ndim > 1 else data
    t0, t1 = int(0.25 * sr), int(0.85 * sr)
    if len(x) < t1:
        t0, t1 = int(0.03 * sr), len(x)
    x = x[t0:t1].astype(np.float64)
    expected = 440 * 2 ** ((key - 69) / 12)
    period = sr / expected
    if len(x) < period * 8:
        return None
    x -= x.mean()
    n = len(x)
    spec = np.fft.rfft(x * np.hanning(n), 2 * n)
    ac = np.fft.irfft(np.abs(spec) ** 2)[:n]
    lo, hi = max(2, int(period / 1.06)), min(n - 2, int(period * 1.06) + 1)
    if hi <= lo or ac[0] <= 0:
        return None
    lag = lo + int(np.argmax(ac[lo:hi]))
    if ac[lag] < 0.5 * ac[0]:  # periodicità debole: misura inaffidabile
        return None
    a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
    den = a - 2 * b + c
    lag = lag + (0.5 * (a - c) / den if den else 0)
    cents = 1200 * np.log2(sr / lag / expected)
    return float(cents) if abs(cents) <= max_cents else None


class Instrument:
    def __init__(self, sfz_file, autotune=False, root=None, cc=None):
        """root: cartella del pacchetto, dove cercare per nome i campioni con percorsi non risolvibili;
        cc: valori predefiniti dei controller (es. {100: 127} per il suono microfonato di Shinyguitar)."""
        sfz_file = Path(sfz_file)
        self.autotune = autotune
        self._tuning_file = sfz_file.parent / ".backingtrack-tuning.json"
        self._tuning, self._tuning_dirty = None, False
        self._base = sfz_file.parent
        control, ops_list = parse(sfz_file)
        default_path = control.get("default_path", "").replace("\\", "/")
        self.cc_defaults = {int(k[6:]): int(float(v)) for k, v in control.items() if k.startswith("set_cc")}
        self.cc_defaults.update(cc or {})
        base = sfz_file.parent
        index = {}
        for p in Path(root or base).rglob("*.wav"):
            index.setdefault(p.name.lower(), p)
        self.regions = []
        for i, ops in enumerate(ops_list):
            if "sample" not in ops:
                continue
            r = Region(ops, base, default_path, i)
            if r.trigger not in ("attack", "first"):
                continue
            if not r.sample.is_file():
                alt = index.get(r.sample.with_suffix(".wav").name.lower())
                if alt is None:
                    continue
                r.sample = alt
            self.regions.append(r)
        if not self.regions:
            raise SongError(_("SFZ senza campioni utilizzabili: %s") % sfz_file)
        self.by_key = {}
        for r in self.regions:
            for k in range(r.lokey, r.hikey + 1):
                self.by_key.setdefault(k, []).append(r)
        self.keys = sorted(self.by_key)
        self.seq = {}
        self._cache = {}

    def select(self, key, vel, rng, cc=None):
        """Region che suonano per (tasto, velocity). Round robin casuale e sequenziale."""
        if key not in self.by_key:
            return []
        ccs = dict(self.cc_defaults)
        ccs.update(cc or {})
        rand = rng.random()
        count = self.seq.get(key, 0)
        self.seq[key] = count + 1
        out, candidates = [], []
        for r in self.by_key[key]:
            if not (r.lovel <= vel <= r.hivel):
                continue
            if any(not (lo <= ccs.get(n, 0) <= hi) for n, (lo, hi) in r.cc.items()):
                continue
            candidates.append(r)
            if not (r.lorand <= rand < r.hirand or (r.hirand >= 1 and rand >= r.lorand)):
                continue
            if r.seq_length > 1 and count % r.seq_length + 1 != r.seq_position:
                continue
            out.append(r)
        if not out and candidates:
            # round robin non installato (setup leggero): uno a caso tra quelli presenti
            out = [rng.choice(candidates)]
        return out

    def tune_correction(self, region):
        """Semitoni da aggiungere per riportare il campione all'intonazione giusta (0 se autotune spento)."""
        if not self.autotune:
            return 0.0
        if self._tuning is None:
            try:
                self._tuning = json.loads(self._tuning_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._tuning = {}
        try:
            rel = region.sample.relative_to(self._base.parent).as_posix()
        except ValueError:
            rel = str(region.sample)
        k = "%s@%d" % (rel, region.center)
        if k not in self._tuning:
            data, sr = self.sample(region)
            cents = pitch_offset_cents(data, sr, region.center) if data is not None else None
            self._tuning[k] = round(cents, 1) if cents is not None else 0.0
            self._tuning_dirty = True
        return -self._tuning[k] / 100

    def save_tuning(self):
        if self._tuning_dirty:
            try:
                self._tuning_file.write_text(json.dumps(self._tuning, indent=0, sort_keys=True), encoding="utf-8")
                self._tuning_dirty = False
            except OSError:
                pass

    def sample(self, region):
        key = region.sample
        if key not in self._cache:
            try:
                self._cache[key] = read_wav(key)
            except (ValueError, OSError) as e:
                raise SongError(_("campione illeggibile %s: %s") % (key, e))
        data, sr = self._cache[key]
        end = region.end if region.end else data.shape[1]
        if region.offset >= end:
            return None, sr
        return data[:, region.offset:end], sr
