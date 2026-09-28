"""Export MIDI (type 1) per usare l'arrangiamento in una DAW."""
import struct

from .arranger import PPQ

CHANNELS = {"guitar": 0, "guitar2": 1, "bass": 2, "drums": 9}
TRACK_NAMES = {"guitar": "Guitar L", "guitar2": "Guitar R", "bass": "Bass", "drums": "Drums"}
AMP_PROGRAM = {"high": 30, "crunch": 29, "blues": 27, "clean": 27, "twang": 27}


def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def _meta(kind, data):
    return b"\xff" + bytes([kind]) + vlq(len(data)) + data


def write_midi(path, arr, title):
    tempo_us = int(60000000 / arr.tempo)
    track0 = [(0, 0, _meta(0x03, title.encode("utf-8"))),
              (0, 0, _meta(0x51, tempo_us.to_bytes(3, "big"))),
              (0, 0, _meta(0x58, b"\x04\x02\x18\x08"))]
    parts = {}
    for n in arr.notes:
        ch = CHANNELS[n.part]
        evs = parts.setdefault(n.part, [])
        if not evs:
            evs.append((0, 0, _meta(0x03, TRACK_NAMES[n.part].encode())))
            if n.part.startswith("guitar"):
                evs.append((0, 0, bytes([0xC0 | ch, AMP_PROGRAM.get(n.bus.split(":")[1], 27)])))
                evs.append((0, 0, bytes([0xB0 | ch, 10, 30 if n.part == "guitar" else 98])))
            elif n.part == "bass":
                evs.append((0, 0, bytes([0xC0 | ch, 32])))
        evs.append((n.start, 2, bytes([0x90 | ch, n.pitch, n.vel])))
        evs.append((n.end, 1, bytes([0x80 | ch, n.pitch, 0])))

    tracks = [track0] + [parts[p] for p in ("guitar", "guitar2", "bass", "drums") if p in parts]
    with open(path, "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ))
        for evs in tracks:
            evs.sort(key=lambda e: (e[0], e[1]))
            data, last = bytearray(), 0
            for tick, _, msg in evs:
                data += vlq(tick - last) + msg
                last = tick
            data += b"\x00\xff\x2f\x00"
            f.write(b"MTrk" + struct.pack(">I", len(data)) + data)
