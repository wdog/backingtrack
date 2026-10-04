"""Sampler: trasforma le note in tracce audio (bus) usando gli strumenti SFZ."""
import math
import random
from fractions import Fraction

import numpy as np

SR = 48000  # come la batteria Salamander: niente conversione sui piatti
MAX_VOICE_S = 8.0


def _smooth(n):
    """Il più piccolo intero >= n senza fattori primi oltre il 7 (FFT veloce)."""
    while True:
        m = n
        for p in (2, 3, 5, 7):
            while m % p == 0:
                m //= p
        if m == 1:
            return n
        n += 1


def resample(data, sr_from, sr_to):
    """Conversione di frequenza di campionamento a banda limitata (FFT, rapporto razionale esatto).

    Molto più pulita dell'interpolazione lineare (niente aliasing sui piatti); il segnale è
    allungato di zeri, così la discontinuità finale non rientra sull'attacco.
    """
    q = Fraction(sr_to, sr_from).limit_denominator(1000)
    up, down = q.numerator, q.denominator
    n = data.shape[1]
    k = _smooth(-(-(n + 1024) // down))
    x = np.fft.rfft(data, k * down, axis=1)
    m = k * up
    y = np.zeros((data.shape[0], m // 2 + 1), dtype=np.complex64)
    w = min(x.shape[1], y.shape[1])
    y[:, :w] = x[:, :w]
    return (np.fft.irfft(y, m, axis=1)[:, : n * up // down] * (up / down)).astype(np.float32)


class Sampler:
    def __init__(self, instrument, sr=SR, vel_exp=1.0, detune=0.0, seed=7):
        self.ins = instrument
        self.sr = sr
        self.vel_exp = vel_exp  # <1 = curva velocity più morbida (ghost note udibili)
        # umanizzazione: ogni voce un filo stonata (-detune, 0 o +detune cent: pochi valori per non
        # moltiplicare la cache dei campioni trasposti) e con volume leggermente diverso;
        # le corde di una chitarra vera non sono mai perfette
        self.detune = detune
        self._human = random.Random(seed)
        self._pitched = {}

    def _pitched_sample(self, region, semitones):
        """Campione trasposto e portato alla frequenza del motore, in cache.

        Solo cambio di frequenza (batteria): FFT a banda limitata. Con trasposizione: interpolazione
        lineare in un passo solo (chitarre e basso, la cui catena taglia comunque gli acuti)."""
        key = (region.sample, region.offset, region.end, round(semitones, 3))
        if key not in self._pitched:
            data, sr = self.ins.sample(region)
            if data is None:
                self._pitched[key] = None
            else:
                ratio = 2 ** (semitones / 12) * sr / self.sr
                data = data[:, : int(MAX_VOICE_S * sr)]
                if abs(semitones) < 1e-3 and sr != self.sr:
                    data = resample(data, sr, self.sr)
                elif abs(ratio - 1) > 1e-6:
                    n = data.shape[1]
                    pos = np.arange(0, n - 1, ratio, dtype=np.float64)
                    xp = np.arange(n)
                    data = np.stack([np.interp(pos, xp, c) for c in data]).astype(np.float32)
                self._pitched[key] = data
        return self._pitched[key]

    def voices(self, notes, rng, cc_for=None):
        """Note -> voci concrete: (inizio_s, fine_s|None, region, dati, gain)."""
        out = []
        for n in notes:
            key, cc = n["key"], None
            if cc_for:
                key, cc = cc_for(key)
            for r in self.ins.select(key, n["vel"], rng, cc):
                semis = key - r.center + r.tune + self.ins.tune_correction(r)
                gain = 10 ** (r.volume / 20) * r.vel_gain(n["vel"]) ** self.vel_exp * n.get("gain", 1.0)
                if self.detune:
                    semis += self._human.choice((-self.detune, 0, self.detune)) / 100
                    gain *= 10 ** (self._human.uniform(-1.5, 1.5) / 20)
                data = self._pitched_sample(r, semis)
                if data is None:
                    continue
                end = None if r.one_shot else n["end"]
                out.append(dict(start=n["start"], end=end, region=r, data=data, gain=gain,
                                muted=n.get("muted", False), bus=n["bus"]))
        # choke: una region con off_by=X si spegne quando parte una region del gruppo X
        by_group = {}
        for v in out:
            if v["region"].group:
                by_group.setdefault(v["region"].group, []).append(v["start"])
        for v in out:
            ob = v["region"].off_by
            if ob and ob in by_group:
                later = [t for t in by_group[ob] if t > v["start"] + 1e-4]
                if later:
                    t = min(later)
                    v["end"] = t if v["end"] is None else min(v["end"], t)
                    v["choke"] = True
        return out


def mix_voices(voices, buses, sr=SR):
    """Somma le voci nei bus (array stereo float32)."""
    for v in voices:
        data = v["data"]
        s = int(round(v["start"] * sr))
        n = data.shape[1]
        r = v["region"]
        release = 0.006 if v.get("choke") and r.off_mode == "fast" else max(r.release, 0.02)
        if v["muted"]:
            release = 0.04 if v["muted"] == "real" else 0.05
        length = n
        if v["end"] is not None:
            length = min(n, int((v["end"] - v["start"]) * sr) + int(release * sr))
        if length <= 0:
            continue
        y = data[:, :length] * v["gain"]
        if v["end"] is not None:
            rel_start = max(0, int((v["end"] - v["start"]) * sr))
            if rel_start < length:
                k = length - rel_start
                y[:, rel_start:] *= np.linspace(1, 0, k, dtype=np.float32) ** 2
        if v["muted"] is True:
            # palm mute simulato (chitarre senza campioni staccato): decadimento rapido e suono più scuro
            t = np.arange(length, dtype=np.float32) / sr
            y = y * np.exp(-t / 0.09)
            k = 12
            kernel = np.ones(k, dtype=np.float32) / k
            y = np.stack([np.convolve(c, kernel, "same") for c in y]) * 1.25
        bus = buses[v["bus"]]
        e = min(s + length, bus.shape[1])
        if e <= s:
            continue
        seg = y[:, : e - s]
        if bus.shape[0] == 1 and seg.shape[0] > 1:
            seg = seg.mean(axis=0, keepdims=True)
        if seg.shape[0] == 1:
            bus[:, s:e] += seg[0]
        else:
            bus[:, s:e] += seg[:2]
    return buses


def new_buses(names, seconds, sr=SR):
    """Bus vuoti: stereo la batteria, mono gli altri (chitarre e basso si spazializzano nel mix)."""
    n = int(math.ceil(seconds * sr))
    return {name: np.zeros((2 if name == "drums" else 1, n), dtype=np.float32) for name in names}


def make_rng(seed):
    return random.Random(seed)
