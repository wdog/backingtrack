"""Mix: simulazione ampli/cassa, EQ, compressione, slapback, riverbero, loudness (via ffmpeg + numpy)."""
import shutil
from concurrent.futures import ThreadPoolExecutor
import subprocess
import wave
from pathlib import Path

import numpy as np

from .i18n import _
from .errors import SongError
from .render import SR

# Ampli: pre = preamp + saturazione (con passa-basso anti-aliasing), ir = cassa vera (convoluzione),
# cab_eq = cassa simulata con EQ se le IR non sono installate, post = timbro finale.
AMPS = {
    "clean": dict(
        pre="highpass=f=70,acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=2,"
            "volume=3dB,asoftclip=type=tanh:threshold=0.9",
        ir="1_Nacho_Guacamole_44.wav", post="equalizer=f=800:t=q:w=1:g=-1.5",
        cab_eq="equalizer=f=110:t=q:w=1:g=2,equalizer=f=800:t=q:w=1:g=-2,equalizer=f=2800:t=q:w=1.2:g=3,"
               "lowpass=f=6500,lowpass=f=7000"),
    "blues": dict(
        pre="highpass=f=90,acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=2,"
            "lowpass=f=6000,volume=8dB,asoftclip=type=tanh",
        ir="3_Wasabi_Warrior_44.wav", post="equalizer=f=1000:t=q:w=1:g=1.5",
        cab_eq="equalizer=f=120:t=q:w=1:g=2,equalizer=f=1000:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1:g=-1,"
               "lowpass=f=5000,lowpass=f=5500"),
    "twang": dict(
        pre="highpass=f=80,acompressor=threshold=0.12:ratio=4:attack=3:release=100:makeup=2,"
            "volume=3dB,asoftclip=type=tanh:threshold=0.85",
        ir="1_Nacho_Guacamole_44.wav", post="equalizer=f=900:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1:g=3",
        cab_eq="equalizer=f=150:t=q:w=1:g=1,equalizer=f=900:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1:g=5,"
               "lowpass=f=8000"),
    "crunch": dict(
        pre="highpass=f=130,lowpass=f=5000,volume=17dB,asoftclip=type=tanh,highpass=f=90",
        ir="5_Don_Spinacio_44.wav", post="equalizer=f=650:t=q:w=1:g=-2",
        cab_eq="equalizer=f=110:t=q:w=1:g=3,equalizer=f=650:t=q:w=1:g=-2,"
               "equalizer=f=1800:t=q:w=1:g=3,lowpass=f=4800,lowpass=f=5200"),
    "high": dict(
        pre="highpass=f=180,lowpass=f=4500,volume=20dB,asoftclip=type=tanh,highpass=f=120,volume=2dB,"
            "asoftclip=type=atan",
        ir="12_World_Collider_44.wav", post="equalizer=f=500:t=q:w=1:g=-4",
        cab_eq="equalizer=f=100:t=q:w=1:g=4,equalizer=f=500:t=q:w=1:g=-5,equalizer=f=2200:t=q:w=1:g=3,"
               "lowpass=f=4200,lowpass=f=4600"),
    # chitarra acustica (microfonata): niente ampli né cassa, solo compressione e un po' di brillantezza
    "acoustic": dict(
        pre="highpass=f=80,acompressor=threshold=0.15:ratio=2.5:attack=8:release=150:makeup=2,"
            "equalizer=f=250:t=q:w=1:g=-2,equalizer=f=5000:t=q:w=1:g=2",
        ir=None, post="", cab_eq=""),
}
PAN = {"L": (0.95, 0.3), "R": (0.3, 0.95), "C": (0.72, 0.69)}
DRUMS_CHAIN = ("acompressor=threshold=0.125:ratio=3:attack=10:release=100:makeup=1.5,"
               "equalizer=f=60:t=q:w=1:g=3,equalizer=f=400:t=q:w=1:g=-3,equalizer=f=5000:t=q:w=1:g=2")
BASS_CHAIN = ("acompressor=threshold=0.1:ratio=4:attack=10:release=150:makeup=2,"
              "equalizer=f=80:t=q:w=1:g=2,lowpass=f=4000")
SLAP = "adelay=110|110,highpass=f=300,lowpass=f=3000,volume=0.35"

# bilanciamento (dBFS RMS) e mandata al riverbero per famiglia di bus
LEVELS = {"guitar": -18.0, "drums": -17.5, "bass": -21.0}
SENDS = {"guitar": 0.22, "drums": 0.12, "bass": 0.0}


def family(bus):
    return "guitar" if bus.startswith("gtr:") else bus


def bus_graph(bus, cab_dir=None):
    """Filtergraph ffmpeg per un bus: ([ingressi extra], grafo con ingresso [0] e uscita [out])."""
    if bus == "drums":
        return [], "[0]%s[out]" % DRUMS_CHAIN
    if bus == "bass":
        return [], "[0]pan=mono|c0=c0,%s,pan=stereo|c0=c0|c1=c0[out]" % BASS_CHAIN
    _, amp, rest = bus.split(":", 2)
    a = AMPS[amp]
    l, r = PAN[rest.split(":")[0]]
    pan = "pan=stereo|c0=%g*c0|c1=%g*c0" % (l, r)
    tail = ",".join(x for x in (a["post"], "highpass=f=70", pan) if x)
    if bus.endswith(":slap"):
        tail += ",asplit[a][b];[b]%s[e];[a][e]amix=inputs=2:normalize=0" % SLAP
    ir = Path(cab_dir) / a["ir"] if cab_dir and a["ir"] else None
    if ir and ir.is_file():
        return [str(ir)], "[0]pan=mono|c0=c0,%s[p];[p][1]afir=dry=10:wet=10[c];[c]%s[out]" % (a["pre"], tail)
    return [], "[0]pan=mono|c0=c0,%s[out]" % ",".join(x for x in (a["pre"], a["cab_eq"], tail) if x)


def rms(x):
    """RMS delle sole parti in cui il bus suona (stima su 1 campione ogni 8)."""
    y = x[:, ::8]
    active = np.abs(y).max(axis=0) > 1e-4
    if not active.any():
        return 0.0
    return float(np.sqrt(np.mean(y[:, active] ** 2)))


def db(v):
    return 10 ** (v / 20)


def reverb_ir(seconds=1.4, rt60=0.9, seed=7):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    env = np.exp(-6.9 * t / rt60)
    ir = rng.standard_normal((2, n)) * env
    k = 6  # tail più scura
    ir = np.stack([np.convolve(c, np.ones(k) / k, "same") for c in ir])
    pre = int(0.012 * SR)
    ir = np.concatenate([np.zeros((2, pre)), ir], axis=1)
    for d, g in ((0.007, 0.5), (0.013, 0.35), (0.021, 0.3), (0.034, 0.2)):  # prime riflessioni
        i = pre + int(d * SR)
        ir[0, i] += g
        ir[1, i + 37] += g * 0.9
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return ir.astype(np.float32)


def write_raw(path, x):
    np.ascontiguousarray(x.T, dtype=np.float32).tofile(path)


def read_raw(path, channels=2):
    return np.fromfile(path, dtype=np.float32).reshape(-1, channels).T


def write_wav16(path, x):
    y = np.clip(x, -1, 1)
    data = (y.T * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise SongError(_("ffmpeg non trovato nel PATH (vedi README, Installazione)"))
    return exe


def _run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                       stdin=subprocess.DEVNULL)
    if p.returncode != 0:
        raise SongError(_("ffmpeg ha fallito:\n%s") % p.stderr[-2500:])


def mix(buses, out_wav, tmp, mp3=None, stems_dir=None, loudness=-16.0, cab_dir=None):
    """buses: {nome: array stereo}. Scrive out_wav (e mp3). Ritorna i livelli usati."""
    ffmpeg = _ffmpeg()
    tmp = Path(tmp)
    raw = ["-f", "f32le", "-ar", str(SR), "-ac", "2"]
    names = [b for b in buses if rms(buses[b]) > 0]
    if not names:
        raise SongError(_("niente da mixare"))

    # 1) catene per bus (ampli, EQ, compressione, slapback), un processo ffmpeg per bus in parallelo
    def process(i, name):
        x = buses[name]
        if family(name) == "guitar":  # livello DI costante = saturazione prevedibile
            x = x * (db(-20) / rms(x))
        # rumore a -140 dB: evita i numeri denormali (lentissimi) nei filtri durante i silenzi
        x = x + np.random.default_rng(i).standard_normal(x.shape).astype(np.float32) * 1e-7
        write_raw(tmp / ("in%d.raw" % i), x)
        extra, graph = bus_graph(name, cab_dir)
        cmd = [ffmpeg, "-y", "-v", "error"] + raw + ["-i", str(tmp / ("in%d.raw" % i))]
        for f in extra:
            cmd += ["-i", f]
        _run(cmd + ["-filter_complex", graph, "-map", "[out]"] + raw[:2] + [str(tmp / ("out%d.raw" % i))])

    with ThreadPoolExecutor(len(names)) as ex:
        list(ex.map(lambda a: process(*a), enumerate(names)))

    # 2) bilanciamento per famiglia + mandata riverbero
    n = max(buses[b].shape[1] for b in names)
    fams = {}
    for i, name in enumerate(names):
        y = read_raw(tmp / ("out%d.raw" % i))
        y = np.pad(y, ((0, 0), (0, max(0, n - y.shape[1]))))[:, :n]
        f = family(name)
        fams[f] = fams[f] + y if f in fams else y
    dry = np.zeros((2, n), dtype=np.float32)
    send = np.zeros((2, n), dtype=np.float32)
    for f, y in fams.items():
        y = y * (db(LEVELS[f]) / max(rms(y), 1e-9))
        fams[f] = y
        dry += y
        send += y * SENDS[f]
    gain = db(loudness) / max(rms(dry), 1e-9)
    write_raw(tmp / "dry.raw", dry)
    write_raw(tmp / "send.raw", send)
    write_raw(tmp / "ir.raw", reverb_ir())

    if stems_dir:
        stems_dir.mkdir(parents=True, exist_ok=True)
        for f, y in fams.items():
            write_wav16(stems_dir / (f + ".wav"), y * gain * 0.7)

    # 3) riverbero, glue, loudness, limiter
    graph = ("[1][2]afir=dry=10:wet=10[wet];[0][wet]amix=inputs=2:normalize=0,"
             "acompressor=threshold=0.25:ratio=2:attack=20:release=200,"
             "volume=%.4f,alimiter=limit=0.891:level=0:attack=3:release=60,asplit=2[m1][m2]" % gain)
    cmd = [ffmpeg, "-y", "-v", "error"]
    for f in ("dry", "send", "ir"):
        cmd += raw + ["-i", str(tmp / (f + ".raw"))]
    cmd += ["-filter_complex", graph, "-map", "[m1]", "-c:a", "pcm_s16le", str(out_wav)]
    if mp3:
        cmd += ["-map", "[m2]", "-c:a", "libmp3lame", "-b:a", "192k", str(mp3)]
    else:
        cmd += ["-map", "[m2]", "-f", "null", "-"]
    _run(cmd)
