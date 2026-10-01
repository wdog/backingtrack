"""Groove: pattern di chitarra e batteria per una battuta di 4/4.

Evento chitarra: (beat, tipo, velocity[, durata in beat])
  D  pennata giù (tutte le corde)       U  pennata su (4 corde alte)
  C  chop: 4 corde alte stoppate        P  power chord
  B / B5  nota di basso: tonica / quinta
  R5 R6 R7  bicordi boogie (tonica + 5a / 6a / 7a minore)
  J  voicing jazz a 4 note (tonica, 7a, 3a, 5a/estensione)
  suffisso "m" = stoppato (palm mute)

Evento batteria: (beat, nota GM, velocity). I beat in levare (.5) vengono spostati dallo swing.
"""
from .errors import SongError

# GM drum map (usato anche per l'export MIDI)
KICK, STICK, SNARE, HH, PEDAL, OHH = 36, 37, 38, 42, 44, 46
LT, MT, HT, CRASH, RIDE, BELL = 45, 47, 50, 49, 51, 53

T1, T2 = 1 / 3, 2 / 3


def hat8(on=90, off=60, note=HH):
    return [(i / 2, note, on if i % 2 == 0 else off) for i in range(8)]


def boogie(pattern, vel=95):
    kinds = {"5": "R5m", "6": "R6m", "7": "R7m"}
    return [(i / 2, kinds[c], vel if i % 2 == 0 else vel - 15) for i, c in enumerate(pattern)]


def hat16(on=80, off=50, note=HH):
    return [(i / 4, note, on if i % 2 == 0 else off) for i in range(16)]


def hits(note, beats, vel=90):
    return [(b, note, vel) for b in beats]


# pattern chitarra in testo: 8 caratteri = ottavi, 12 = terzine, 16 = sedicesimi (spazi ignorati).
# Maiuscola = forte, minuscola = piano. D/d giù, U/u su, X/x chop, M/m giù stoppato, N/n su stoppato,
# P power chord, p power chord stoppato, J/j jazz, B/b tonica, F/f quinta; "." pausa, "-" tiene la nota.
PAT = {"D": "D", "U": "U", "X": "C", "M": "Dm", "N": "Um", "P": "P", "J": "J", "B": "B", "F": "B5"}


def pat(text, loud=100, soft=68, dur=None):
    text = text.replace(" ", "")
    step = 4 / len(text)
    out = []
    for i, ch in enumerate(text):
        if ch in ".-":
            continue
        kind = PAT[ch.upper()]
        if ch == "p":
            kind = "Pm"
        n = 1
        while i + n < len(text) and text[i + n] == "-":
            n += 1
        length = None
        if i + n < len(text) and text[i + n] == ".":
            length = n * step
        if dur is not None:
            length = min(length or 4, dur)
        out.append((i * step, kind, loud if ch.isupper() else soft, length))
    return out


ROCK_BEAT = ([(0, KICK, 110), (2, KICK, 105), (2.5, KICK, 90), (1, SNARE, 112), (3, SNARE, 112),
              (1.75, SNARE, 25)] + hat8())
ROCK_TURN = [(3, SNARE, 112), (3, HH, 85), (3.5, OHH, 90), (3.5, KICK, 95)]
ROCK_FILL = [(2, SNARE, 95), (2.5, SNARE, 100), (3, HT, 105), (3.25, HT, 90),
             (3.5, MT, 105), (3.75, LT, 110), (2, KICK, 100), (3, KICK, 100)]

BALLAD_BEAT = [(0, KICK, 105), (2.5, KICK, 85), (2, SNARE, 110)] + hat8(75, 50)
BALLAD_TURN = [(3, KICK, 90), (3.5, SNARE, 70), (3.75, SNARE, 85), (3, HH, 70), (3.5, OHH, 70)]
BALLAD_FILL = [(3, SNARE, 90), (3.25, SNARE, 80), (3.5, HT, 100), (3.75, LT, 105)]

SHUFFLE_BEAT = ([(0, KICK, 105), (2, KICK, 100), (1, SNARE, 108), (3, SNARE, 108),
                 (1 + T2, SNARE, 28)] + hat8(85, 55))
SHUFFLE_TURN = [(3, SNARE, 108), (3, HH, 85), (3 + T1, SNARE, 40), (3 + T2, SNARE, 75), (3 + T2, KICK, 80)]
SHUFFLE_FILL = [(3, SNARE, 90), (3 + T1, SNARE, 70), (3 + T2, SNARE, 105), (3, KICK, 95)]

TRAIN_BEAT = ([(0, KICK, 100), (2, KICK, 95), (1, PEDAL, 60), (3, PEDAL, 60)] +
              [(i / 2, SNARE, 108 if i in (2, 6) else 42) for i in range(8)])
TRAIN_TURN = [(3, SNARE, 110), (3, PEDAL, 60), (3.5, SNARE, 95), (3.5, KICK, 85)]

BILLY_BEAT = ([(0, KICK, 100), (2, KICK, 95), (1, SNARE, 108), (3, SNARE, 108), (3.5, SNARE, 45)] +
              hat8(85, 60))

SLOW_BEAT = ([(0, KICK, 95), (2, KICK, 90), (2 + T2, KICK, 60), (1, SNARE, 100), (3, SNARE, 100)] +
             [(b + k / 3, RIDE, (78, 45, 60)[k]) for b in range(4) for k in range(3)])
SLOW_TURN = [(3, SNARE, 100), (3, RIDE, 78), (3 + T1, RIDE, 45), (3 + T2, SNARE, 60), (3 + T2, KICK, 70)]
SLOW_FILL = [(2, SNARE, 80), (2 + T1, SNARE, 65), (2 + T2, SNARE, 90),
             (3, HT, 95), (3 + T1, MT, 95), (3 + T2, LT, 105), (2, KICK, 90)]

HALFTIME_BEAT = [(0, KICK, 112), (1.5, KICK, 95), (2, SNARE, 118)] + hat8(92, 62)
HALFTIME_TURN = [(3, SNARE, 90), (3.25, SNARE, 70), (3.5, SNARE, 100), (3.75, SNARE, 110), (3, KICK, 90)]
GALLOP_BEAT = ([(b + d, KICK, 105 if d == 0 else 85) for b in (0, 2) for d in (0, 0.5, 0.75)] +
               [(1, SNARE, 115), (3, SNARE, 115)] + hat8(90, 60))
RHUMBA_BEAT = ([(0, KICK, 100), (1.5, KICK, 88), (2, KICK, 95), (3.5, KICK, 85),
                (1, STICK, 95), (2.5, STICK, 70), (3, STICK, 100)] + hat8(80, 55))
RHUMBA_TURN = [(3, STICK, 100), (3, KICK, 90), (3.5, LT, 90), (3.75, LT, 100)]
FUNK_BEAT = ([(0, KICK, 110), (0.75, KICK, 85), (2.5, KICK, 95), (1, SNARE, 112), (3, SNARE, 112),
              (1.75, SNARE, 35), (3.25, SNARE, 30), (3.5, OHH, 70)] +
             [(i / 4, HH, 85 if i % 2 == 0 else 45) for i in range(16) if i != 14])
FUNK_TURN = [(3, SNARE, 112), (3.25, SNARE, 60), (3.5, SNARE, 80), (3.75, SNARE, 95), (3, KICK, 90)]
# jazz: ride "ding ding-da", charleston sul pedale (2 e 4), cassa piuma
JAZZ_RIDE = [(0, RIDE, 95), (1, RIDE, 100), (1 + T2, RIDE, 65), (2, RIDE, 92), (3, RIDE, 100), (3 + T2, RIDE, 65)]
JAZZ_BEAT = JAZZ_RIDE + [(1, PEDAL, 75), (3, PEDAL, 75)] + [(b, KICK, 38) for b in range(4)]
JAZZ_TURN = [(2 + T2, SNARE, 55), (3 + T2, SNARE, 80), (3 + T2, KICK, 70)]
JAZZ_FILL = [(2, SNARE, 70), (2 + T2, SNARE, 60), (3, SNARE, 85), (3 + T1, MT, 80), (3 + T2, LT, 95), (3, KICK, 70)]
JAZZ_BALLAD = ([(b, SNARE, 30) for b in range(4)] + [(b + T2, SNARE, 18) for b in range(4)] +
               [(0, RIDE, 60), (2, RIDE, 60), (1, PEDAL, 55), (3, PEDAL, 55), (0, KICK, 35)])
JAZZ_BALLAD_TURN = [(3, SNARE, 40), (3 + T2, SNARE, 50)]
BOSSA_BEAT = ([(0, KICK, 85), (1.5, KICK, 70), (2, KICK, 85), (3.5, KICK, 70),
               (0, STICK, 80), (1.5, STICK, 75), (3, STICK, 80)] + hat8(55, 40))
BOSSA_TURN = [(2.5, STICK, 75), (3, STICK, 80), (3.5, KICK, 75)]
BOSSA_FILL = [(3, STICK, 85), (3.5, LT, 75), (3.75, LT, 85), (3, KICK, 80)]
STOP_BEAT = [(0, KICK, 118), (0, SNARE, 90), (0, CRASH, 90), (1, HH, 45), (2, HH, 45), (3, HH, 45)]
COUNTRY_BEAT = ([(0, KICK, 95), (2, KICK, 90), (1, SNARE, 100), (3, SNARE, 100)] +
                [(i / 2, SNARE, 30) for i in (1, 3, 5, 7)] + hat8(70, 45, PEDAL))
# reggae one drop: niente cassa sull'1, cassa + cross-stick sul 3
ONEDROP_BEAT = [(2, KICK, 105), (2, STICK, 100), (0, HH, 70)] + [(b + T2, HH, 50) for b in range(4)] + \
               [(b, HH, 70) for b in (1, 2, 3)]
ONEDROP_TURN = [(3, STICK, 90), (3 + T2, STICK, 70), (3.5, LT, 80), (3 + T2, KICK, 70)]
ONEDROP_FILL = [(2, SNARE, 85), (2 + T2, SNARE, 70), (3, HT, 90), (3 + T1, MT, 90), (3 + T2, LT, 100)]
SKA_BEAT = ([(0, KICK, 100), (2, KICK, 95), (1, SNARE, 105), (3, SNARE, 105)] +
            [(b + 0.5, OHH, 70) for b in range(4)] + [(b, PEDAL, 55) for b in range(4)])
DISCO_BEAT = ([(b, KICK, 108) for b in range(4)] + [(1, SNARE, 105), (3, SNARE, 105)] +
              [(b, HH, 70) for b in range(4)] + [(b + 0.5, OHH, 82) for b in range(4)])
# soul / Motown: rullante su tutti e 4 i tempi, cassa piena
MOTOWN_BEAT = ([(0, KICK, 105), (1.5, KICK, 80), (2, KICK, 100), (3.5, KICK, 75)] +
               [(b, SNARE, 108 if b % 2 else 80) for b in range(4)] + hat8(80, 55))
DOOWOP_BEAT = ([(0, KICK, 90), (2, KICK, 85), (1, SNARE, 95), (3, SNARE, 95)] +
               [(b + k / 3, RIDE, (70, 40, 52)[k]) for b in range(4) for k in range(3)])

STRUM_DDU = [(0, "D", 110), (1, "D", 95), (1.5, "U", 75), (2.5, "U", 80), (3, "D", 95), (3.5, "U", 75)]

# amp: clean | blues | twang | crunch | high     double: chitarra doppiata L/R
# voicing (accordi D/U/C): barre (default) | open | jazz | triad — il brano può cambiarlo con voicing:
GROOVES = {
    "rock": dict(
        desc="Rock: power chord a ottavi con palm mute, ampli distorto, chitarre doppiate",
        amp="high", double=True, swing=0, bass_style="eighths",
        guitar=[(0, "P", 118, 0.5)] + [(i / 2, "Pm", 88 if i % 2 else 102) for i in range(1, 8)],
        drums=ROCK_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "rock/strum": dict(
        voicing="open",
        desc="Rock: accordi aperti D . D U . U D U, crunch, chitarre doppiate",
        amp="crunch", double=True, swing=0, bass_style="eighths",
        guitar=STRUM_DDU, drums=ROCK_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "rock/drive": dict(
        desc="Rock: pennate giù a ottavi, accordi pieni (punk/drive)",
        amp="crunch", double=True, swing=0, bass_style="eighths",
        guitar=[(i / 2, "D", 105 if i % 2 == 0 else 88) for i in range(8)],
        drums=ROCK_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "rock/ballad": dict(
        voicing="open",
        desc="Rock ballad: accordi lunghi e pennate leggere, batteria half-time",
        amp="clean", double=False, swing=0, bass_style="slow",
        guitar=[(0, "D", 105), (1.5, "U", 60), (2, "D", 85), (2.5, "U", 65), (3.5, "U", 60)],
        drums=BALLAD_BEAT, turn=BALLAD_TURN, fill=BALLAD_FILL),
    "rock/halftime": dict(
        desc="Rock: half-time pesante, power chord lunghi e rullante sul 3",
        amp="high", double=True, swing=0, bass_style="slow",
        guitar=[(0, "P", 118, 1.9), (2, "P", 108, 1.4), (3.5, "Pm", 95)],
        drums=HALFTIME_BEAT, turn=HALFTIME_TURN, fill=ROCK_FILL),
    "rock/gallop": dict(
        desc="Rock: galoppo (ottavo + due sedicesimi) in palm mute, stile heavy metal classico",
        amp="high", double=True, swing=0, bass_style="eighths",
        guitar=[(b + d, "P" if (b, d) == (0, 0) else "Pm", 110 if d == 0 else 88, 0.25 if (b, d) == (0, 0) else None)
                for b in range(4) for d in (0, 0.5, 0.75)],
        drums=GALLOP_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "rock/pop": dict(
        voicing="open",
        desc="Pop-rock: pennate a sedicesimi D D DU DU, crunch leggero",
        amp="crunch", double=True, swing=0, bass_style="eighths",
        guitar=[(0, "D", 105), (0.5, "D", 78), (1, "D", 95), (1.5, "U", 70), (1.75, "U", 58), (2, "D", 98),
                (2.5, "D", 78), (3, "D", 95), (3.5, "U", 70), (3.75, "U", 58)],
        drums=ROCK_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "blues": dict(
        desc="Blues: shuffle boogie 5-6 (stile Jimmy Reed)",
        amp="blues", double=False, swing=1, bass_style="walk", mute_len=0.4,
        guitar=boogie("55665566"),
        drums=SHUFFLE_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
    "blues/7": dict(
        desc="Blues: shuffle boogie 5-6-b7-6",
        amp="blues", double=False, swing=1, bass_style="walk", mute_len=0.4,
        guitar=boogie("55667766"),
        drums=SHUFFLE_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
    "blues/strum": dict(
        desc="Blues: accordi pieni in shuffle (D . D U . U D U)",
        amp="blues", double=False, swing=1, bass_style="walk",
        guitar=STRUM_DDU, drums=SHUFFLE_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
    "blues/slow": dict(
        desc="Blues lento 12/8: pennate sulle terzine, ride",
        amp="blues", double=False, swing=0, bass_style="slow",
        guitar=[(0, "D", 100)] + [(b + T2, "U", 60) for b in range(4)] + [(b, "D", 80) for b in (1, 2, 3)],
        drums=SLOW_BEAT, turn=SLOW_TURN, fill=SLOW_FILL),
    "blues/rhumba": dict(
        desc="Blues rhumba: boogie dritto con ritmo latino e side-stick",
        amp="blues", double=False, swing=0, bass_style="walk", mute_len=0.35,
        guitar=boogie("55665566"),
        drums=RHUMBA_BEAT, turn=RHUMBA_TURN, fill=SHUFFLE_FILL),
    "blues/funk": dict(
        desc="Funk blues: chop a sedicesimi (chicken scratch) su accordi di nona",
        amp="clean", double=False, swing=0, bass_style="eighths",
        guitar=[(0, "D", 100, 0.2), (0.5, "C", 70), (0.75, "C", 85), (1, "C", 100), (1.5, "C", 65), (1.75, "C", 80),
                (2, "D", 95, 0.2), (2.5, "C", 70), (3, "C", 100), (3.25, "C", 65), (3.5, "C", 80)],
        drums=FUNK_BEAT, turn=FUNK_TURN, fill=ROCK_FILL),
    "blues/stop": dict(
        desc="Blues stop-time: un colpo secco sul primo tempo, poi silenzio (per le strofe cantate)",
        amp="blues", double=False, swing=1, bass_style="stop",
        guitar=[(0, "D", 118, 0.6)],
        drums=STOP_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
    "rockabilly": dict(
        desc="Rockabilly: boom-chick (basso/accordo) + train beat, slapback",
        amp="twang", double=False, swing=0.5, bass_style="rootfifth", slap=True,
        guitar=[(0, "B", 105), (1, "C", 98), (1.5, "C", 65), (2, "B5", 100), (3, "C", 98), (3.5, "C", 65)],
        drums=TRAIN_BEAT, turn=TRAIN_TURN, fill=SHUFFLE_FILL),
    "rockabilly/boogie": dict(
        desc="Rockabilly: boogie 5-6 swing veloce, slapback",
        amp="twang", double=False, swing=0.6, bass_style="walk", slap=True, mute_len=0.35,
        guitar=boogie("55665566", 100),
        drums=BILLY_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
    "rockabilly/strum": dict(
        desc="Rockabilly: accordi pieni sul battere, chop su 2 e 4, slapback",
        amp="twang", double=False, swing=0.6, bass_style="walk", slap=True,
        guitar=[(0, "D", 102), (0.5, "Um", 55), (1, "C", 105), (1.5, "Um", 55),
                (2, "D", 98), (2.5, "Um", 55), (3, "C", 105), (3.5, "Um", 55)],
        drums=BILLY_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
    "country": dict(
        voicing="open",
        desc="Country: boom-chick dritto, basso alternato e spazzolata sul 2 e 4",
        amp="twang", double=False, swing=0, bass_style="rootfifth",
        guitar=[(0, "B", 100), (1, "C", 95), (2, "B5", 98), (3, "C", 95), (3.5, "Um", 55)],
        drums=COUNTRY_BEAT, turn=TRAIN_TURN, fill=SHUFFLE_FILL),
    "country/shuffle": dict(
        voicing="open",
        desc="Country shuffle: boom-chick in swing, stile Texas / honky-tonk",
        amp="twang", double=False, swing=0.7, bass_style="walk",
        guitar=[(0, "B", 100), (1, "C", 95), (1.5, "Um", 55), (2, "B5", 98), (3, "C", 95), (3.5, "Um", 55)],
        drums=SHUFFLE_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
}


GROOVES.update({
    "jazz": dict(
        voicing="jazz",
        desc="Jazz swing: comping a semiminime alla Freddie Green, ride e walking bass",
        amp="clean", double=False, swing=1, bass_style="walk",
        guitar=[(b, "J", 88 if b % 2 == 0 else 80, 0.55) for b in range(4)],
        drums=JAZZ_BEAT, turn=JAZZ_TURN, fill=JAZZ_FILL),
    "jazz/charleston": dict(
        voicing="jazz",
        desc="Jazz swing: comping Charleston (1 e levare del 2), accordi corti",
        amp="clean", double=False, swing=1, bass_style="walk",
        guitar=[(0, "J", 90, 0.4), (1.5, "J", 82, 0.4)],
        drums=JAZZ_BEAT, turn=JAZZ_TURN, fill=JAZZ_FILL),
    "jazz/ballad": dict(
        voicing="jazz",
        desc="Jazz ballad: accordi lunghi e morbidi, spazzole, basso in due",
        amp="clean", double=False, swing=1, bass_style="slow",
        guitar=[(0, "J", 80, 1.9), (2, "J", 68, 1.9)],
        drums=JAZZ_BALLAD, turn=JAZZ_BALLAD_TURN, fill=JAZZ_BALLAD_TURN),
    "jazz/bossa": dict(
        voicing="jazz",
        desc="Bossa nova: basso alternato col pollice e accordi sincopati, cross-stick",
        amp="clean", double=False, swing=0, bass_style="rootfifth",
        guitar=[(0, "B", 88), (1, "J", 70, 0.45), (1.5, "J", 72, 0.45), (2, "B5", 84),
                (2.5, "J", 70, 0.45), (3.5, "J", 74, 0.45)],
        drums=BOSSA_BEAT, turn=BOSSA_TURN, fill=BOSSA_FILL),
})


# ---------------------------------------------------------------- batterie per i groove aggiunti
PUNK_BEAT = hits(KICK, range(4), 108) + hits(SNARE, (0.5, 1.5, 2.5, 3.5), 105) + hat8(95, 75)
CAJUN_BEAT = hits(KICK, range(4), 92) + hits(SNARE, (0.5, 1.5, 2.5, 3.5), 80) + hits(PEDAL, range(4), 50)
# clave 3-2 in una battuta: 1, 1e&, 2&, 3&, 4 (Bo Diddley)
CLAVE = (0, 0.75, 1.5, 2.5, 3)
DIDDLEY_BEAT = ([(0, LT, 108), (0.75, LT, 90), (1.5, LT, 98), (2.5, MT, 95), (3, MT, 102)] +
                hits(KICK, (0, 1.5), 95) + hat16(55, 35))
DIDDLEY_TURN = [(3, MT, 100), (3.25, MT, 80), (3.5, LT, 100), (3.75, LT, 105)]
GLAM_BEAT = ([(0, KICK, 112), (0.5, KICK, 85), (2, KICK, 112), (2.5, KICK, 85)] +
             [(1, SNARE, 118), (1, LT, 100), (3, SNARE, 118), (3, LT, 100)] + hits(HH, range(4), 80))
SURF_BEAT = hits(KICK, (0, 2), 100) + hits(SNARE, (1, 3), 108) + hat8(80, 55, RIDE) + hits(LT, (1.5, 3.5), 70)
ARENA_BEAT = (hits(KICK, (0, 1.5, 2), 110) + hits(SNARE, (1, 3), 115) + hat8(85, 60, RIDE) +
              hits(BELL, (0, 2), 70))
GRUNGE_BEAT = hits(KICK, (0, 0.75, 2.5), 112) + hits(SNARE, (1, 3), 118) + hat8(85, 70, OHH)
HILL_BEAT = hits(KICK, (0, 0.5, 2, 2.5), 100) + hits(SNARE, (1, 3), 105) + hat8(88, 65)
# half-time shuffle alla Purdie: rullante sul 3, ghost note sulle terzine centrali
PURDIE_BEAT = ([(0, KICK, 108), (1 + T2, KICK, 75), (2, SNARE, 115), (3 + T2, KICK, 72)] +
               [(b + k / 3, HH, (85, 0, 60)[k]) for b in range(4) for k in (0, 2)] +
               hits(SNARE, (T1, 1 + T1, 3 + T1), 28))
DELTA_BEAT = hits(KICK, (0, 2), 82) + hits(SNARE, (1, 3), 68) + hits(PEDAL, (1, 3), 50)
JUMP_BEAT = (JAZZ_RIDE + hits(SNARE, (1, 3), 92) + hits(KICK, (0, 2), 78) + hits(PEDAL, (1, 3), 68))
JUNGLE_BEAT = ([(b, LT, 108 if b % 2 == 0 else 92) for b in range(4)] + hits(LT, (0.5, 1.5, 2.5, 3.5), 62) +
               hits(KICK, range(4), 88))
BLUEGRASS_BEAT = hits(KICK, (0, 2), 68) + hits(SNARE, (1, 3), 62) + hits(PEDAL, (0.5, 1.5, 2.5, 3.5), 40)
COWBOY_BEAT = ([(b + d, LT, 100 if d == 0 else 72) for b in range(4) for d in (0, 0.5, 0.75)] +
               hits(KICK, (0, 2), 95) + hits(SNARE, (1, 3), 80))
STOMP_BEAT = hits(KICK, range(4), 110) + hits(SNARE, (1, 3), 118) + hat8(70, 55)
BRUSH_BEAT = (hits(SNARE, range(4), 45) + hits(SNARE, [b + T2 for b in range(4)], 28) +
              hits(PEDAL, (1, 3), 60) + hits(KICK, range(4), 32))
BRUSH_TURN = [(3, SNARE, 60), (3 + T1, SNARE, 45), (3 + T2, SNARE, 70)]
LATINJ_BEAT = (hits(BELL, (0, 1, 1.5, 2.5, 3), 90) + hits(BELL, (0.5, 2, 3.5), 62) +
               hits(KICK, (1.5, 3.5), 90) + hits(STICK, CLAVE, 75))
LATIN_TURN = [(3, MT, 95), (3.25, MT, 80), (3.5, LT, 100), (3.75, LT, 105)]
SAMBA_BEAT = (hits(KICK, range(4), 95) + hits(KICK, (0.75, 1.75, 2.75, 3.75), 65) +
              [(i / 4, HH, 80 if i % 4 == 3 else 48) for i in range(16)] + hits(STICK, (0, 0.75, 1.5, 2.5, 3.25), 78))
FAST_BEAT = JAZZ_BEAT + [(1 + T2, SNARE, 42), (2 + T2, SNARE, 35)]
# 6/8 afro-cubano: ogni tempo è una terzina, campana sul pattern standard a 12
AFRO_BEAT = ([(k / 3, BELL, 92 if k in (0, 6) else 70) for k in (0, 2, 4, 5, 7, 9, 11)] +
             hits(KICK, (0, 2), 90) + hits(STICK, (1 + T1, 3 + T1), 70) + hits(LT, (1 + T2, 3 + T2), 75))
CHA_BEAT = ([(b, BELL, 92 if b % 2 == 0 else 76) for b in range(4)] + hits(KICK, (0, 2), 85) +
            [(1, STICK, 88), (3, LT, 88), (3.5, LT, 95)] + hat8(50, 40))
FUNK2_BEAT = (hits(KICK, (0, 1.5, 1.75, 2.5), 108) + hits(SNARE, (1, 3), 112) + hits(SNARE, (0.75, 2.25, 3.75), 30) +
              hat16(82, 45))
SLOWFUNK_BEAT = hits(KICK, (0, 0.75, 2.5, 2.75), 105) + hits(SNARE, (2,), 115) + hits(SNARE, (1.25, 3.5), 30) + hat16(78, 42)
GOGO_BEAT = (hits(KICK, (0, 1.5, 2.5), 105) + hits(SNARE, (1,), 108) + hits(STICK, (3,), 95) +
             hits(BELL, (0, 0.5, 1.5, 2, 3), 78) + hat8(70, 50))
BOOGALOO_BEAT = (hits(KICK, (0, 0.75, 2.5), 105) + hits(SNARE, (1, 3), 110) + hits(SNARE, (1.75, 3.75), 40) +
                 hat8(82, 55) + [(3.5, OHH, 75)])
LOWRIDER_BEAT = hits(KICK, (0, 2, 2.5), 100) + hits(SNARE, (1, 3), 100) + hits(BELL, range(4), 85) + hat8(70, 50)
POP_BEAT = hits(KICK, (0, 1.5, 2), 105) + hits(SNARE, (1, 3), 108) + hat16(70, 40)
ROCKERS_BEAT = hits(KICK, (0, 2), 102) + hits(SNARE, (2,), 100) + hits(STICK, (1, 3), 60) + hat8(72, 55)
STEPPERS_BEAT = hits(KICK, range(4), 105) + hits(STICK, (1, 3), 95) + hat16(65, 40)
DEMBOW_BEAT = hits(KICK, range(4), 105) + hits(SNARE, (0.75, 1.5, 2.75, 3.5), 100) + hat8(70, 50)
CALYPSO_BEAT = hits(KICK, range(4), 100) + hits(STICK, (0.75, 1.5, 2.75, 3.5), 88) + hits(OHH, (0.5, 1.5, 2.5, 3.5), 72)
ONEDROP8_BEAT = hits(KICK, (2,), 105) + hits(STICK, (2,), 100) + hat8(80, 60)
MEMPHIS_BEAT = hits(KICK, (0, 1.5, 2.5), 102) + hits(SNARE, (1, 3), 110) + hat8(78, 55)
NORTHERN_BEAT = hits(KICK, range(4), 100) + [(b, SNARE, 108 if b % 2 else 85) for b in range(4)] + hat8(85, 60)
PHILLY_BEAT = hits(KICK, range(4), 100) + hits(SNARE, (1, 3), 100) + hat16(65, 40) + hits(OHH, (0.5, 1.5, 2.5, 3.5), 70)
NEO_BEAT = hits(KICK, (0, 0.75, 2.5), 100) + hits(STICK, (1, 3), 100) + hat8(70, 45) + hits(SNARE, (1.75, 3.25), 25)
SPECTOR_BEAT = hits(KICK, (0, 1.5, 2), 110) + hits(SNARE, (3,), 115) + hat8(80, 60)


def g(desc, amp, guitar, drums, turn=ROCK_TURN, fill=ROCK_FILL, bass="eighths", swing=0, **kw):
    return dict(desc=desc, amp=amp, double=kw.pop("double", False), swing=swing, bass_style=bass,
                guitar=guitar, drums=drums, turn=turn, fill=fill, **kw)


SH = dict(turn=SHUFFLE_TURN, fill=SHUFFLE_FILL)
JZ = dict(turn=JAZZ_TURN, fill=JAZZ_FILL)
OD = dict(turn=ONEDROP_TURN, fill=ONEDROP_FILL)
LT_ = dict(turn=LATIN_TURN, fill=LATIN_TURN)

GROOVES.update({
    # ---------------------------------------------------------------- rock
    "rock/shuffle": g("Rock: boogie shuffle distorto in palm mute (stile ZZ Top / Status Quo)", "crunch",
                      boogie("55665566", 102), SHUFFLE_BEAT, bass="walk", swing=1, double=True, mute_len=0.4, **SH),
    "rock/punk": g("Punk: power chord a ottavi tutti in giù, batteria in levare a tutta velocità", "high",
                   pat("PPPPPPPP", 112), PUNK_BEAT, double=True),
    "rock/diddley": g("Bo Diddley beat: clave 3-2 sui tom e accordi sulla clave", "twang",
                      pat("D..D..D...D.D...", 105, dur=0.4), DIDDLEY_BEAT, DIDDLEY_TURN, bass="dotted", slap=True),
    "rock/glam": g("Glam stomp: power chord in quarti e cassa/tom pesanti (anni '70)", "crunch",
                   pat("P-P-P-P-", 112), GLAM_BEAT, bass="quarters", double=True),
    "rock/chug": g("Rock: chug a sedicesimi in palm mute, accento sul primo (hard rock / metal)", "high",
                   pat("Pppppppppppppppp", 112, 88), ROCK_BEAT, double=True),
    "rock/arena": g("Arena rock: accordi aperti 3-3-2 lasciati suonare, ride e cassa larga", "crunch",
                    pat("D--D--D-", 108), ARENA_BEAT, bass="dotted", double=True, voicing="open"),
    "rock/grunge": g("Grunge: power chord sincopati, hi-hat aperto sporco", "high",
                     pat("P..P..P.P-..P-..", 115), GRUNGE_BEAT, double=True),
    "rock/surf": g("Surf: tremolo picking sulla tonica a sedicesimi, ride e tom (stile Misirlou)", "twang",
                   [(i / 4, "B", 100 if i % 4 == 0 else 72, 0.24) for i in range(16)], SURF_BEAT, slap=True),
    "rock/southern": g("Southern rock: accordi aperti D . D U D U D u con un filo di swing", "crunch",
                       pat("D.DUDUDu", 105, 72), ROCK_BEAT, bass="rootfifth", swing=0.35, double=True, voicing="open"),
    # ---------------------------------------------------------------- blues
    "blues/train": g("Blues: boogie in levare leggero sul train beat (Mystery Train, Chicago veloce)", "blues",
                     boogie("55665566", 98), TRAIN_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="rootfifth", swing=0.5,
                     mute_len=0.35),
    "blues/texas": g("Texas shuffle: accordo su ogni tempo e levare stoppato (stile Stevie Ray Vaughan)", "crunch",
                     pat("DnDnDnDn", 102, 55), SHUFFLE_BEAT, bass="walk", swing=1, **SH),
    "blues/jump": g("Jump blues: chop su 2 e 4, ride swing e walking (anni '40)", "clean",
                    pat("d.X.d.X.", 100, 70, dur=0.4), JUMP_BEAT, bass="walk", swing=1, voicing="jazz", **JZ),
    "blues/minor": g("Blues minore lento 12/8: tonica e quinta col pollice, accordo sulle terzine", "blues",
                     pat("BuuFuuBuuFuu", 95, 55), SLOW_BEAT, SLOW_TURN, SLOW_FILL, bass="slow"),
    "blues/delta": g("Delta blues: pollice alternato e chop in levare, batteria leggera", "clean",
                     pat("BxFxBxFx", 95, 65), DELTA_BEAT, BRUSH_TURN, SHUFFLE_FILL, bass="rootfifth", swing=1,
                     voicing="open"),
    "blues/hill": g("Hill country blues: boogie ipnotico dritto, cassa doppia (stile R.L. Burnside)", "crunch",
                    boogie("55555577", 100), HILL_BEAT),
    "blues/halfshuffle": g("Blues: half-time shuffle alla Purdie, ghost note sul rullante", "blues",
                           boogie("55665566"), PURDIE_BEAT, SHUFFLE_TURN, SHUFFLE_FILL, bass="walk", swing=1,
                           mute_len=0.4),
    "blues/chicago": g("Chicago blues: accordo lungo su 1 e 3, chop su 2 e 4", "blues",
                       pat("D-X-D-X-", 100), SHUFFLE_BEAT, bass="walk", swing=1, **SH),
    # ---------------------------------------------------------------- rockabilly
    "rockabilly/slap": g("Rockabilly: pollice tonica/quinta e levare stoppati, slap", "twang",
                         pat("BnXnFnXn", 100, 60), BILLY_BEAT, bass="walk", swing=0.6, slap=True, **SH),
    "rockabilly/stroll": g("Rockabilly lento: accordo, chop e levare stoppato, swing pieno", "twang",
                           pat("D.XnD.Xn", 95, 55), SHUFFLE_BEAT, bass="walk", swing=1, slap=True, **SH),
    "rockabilly/train": g("Rockabilly: basso alternato e pennate stoppate sul train beat (Sun Records)", "twang",
                          pat("BmFmBmFm", 100, 65), TRAIN_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="rootfifth",
                          swing=0.4, slap=True),
    "rockabilly/stop": g("Rockabilly stop-time: colpo sul primo tempo e ripresa sul levare del 4", "twang",
                         [(0, "D", 118, 0.6), (3.5, "U", 90, 0.4)], STOP_BEAT, SHUFFLE_TURN, SHUFFLE_FILL,
                         bass="stop", swing=0.6, slap=True),
    "rockabilly/twist": g("Twist: accordi e chop dritti, rullante su 2 e 4 (primi anni '60)", "twang",
                          pat("D.XUD.XU", 100, 70), BILLY_BEAT, bass="rootfifth", slap=True),
    "rockabilly/jive": g("Jive: boogie 5-6-b7-6 su ride swing, slapback", "twang",
                         boogie("55667766", 100), JUMP_BEAT, bass="walk", swing=1, slap=True, mute_len=0.35, **JZ),
    "rockabilly/psycho": g("Psychobilly: power chord a ottavi, batteria in levare velocissima", "crunch",
                           pat("PPPPPPPP", 110), PUNK_BEAT, slap=True),
    "rockabilly/latin": g("Rockabilly latino: basso e chop sulla clave, tom", "twang",
                          pat("B..X..F...X.X...", 100), DIDDLEY_BEAT, DIDDLEY_TURN, bass="tumbao", slap=True),
    "rockabilly/ballad": g("Ballad anni '50 in 12/8: accordi sulle terzine, slapback", "twang",
                           pat("DuuDuuDuuDuu", 92, 55), DOOWOP_BEAT, SLOW_TURN, SLOW_FILL, bass="slow", slap=True),
    "rockabilly/hillbilly": g("Hillbilly boogie: boogie 5-6 su batteria country, mezzo swing", "twang",
                              boogie("55665566", 98), COUNTRY_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="walk",
                              swing=0.5, slap=True, mute_len=0.35),
    "rockabilly/shuffle": g("Rockabilly shuffle: solo chop su 2 e 4, spazio al contrabbasso", "twang",
                            pat("..X...X.", 105), SHUFFLE_BEAT, bass="walk", swing=1, slap=True, **SH),
    "rockabilly/sun": g("Stile Scotty Moore: tonica, accordo e quinta con levare stoppati", "twang",
                        pat("BnDnFnDn", 100, 55), TRAIN_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="rootfifth",
                        swing=0.3, slap=True),
    "rockabilly/chuck": g("Rock'n'roll alla Chuck Berry: boogie 5-6 dritto e crunch", "crunch",
                          boogie("55665566", 105), BILLY_BEAT, mute_len=0.35),
    "rockabilly/jungle": g("Jungle beat: timpano a ottavi, accordi lunghi su 1 e 3", "twang",
                           [(0, "D", 105, 1.5), (2, "D", 100, 1.5)], JUNGLE_BEAT, DIDDLEY_TURN, bass="walk",
                           swing=1, slap=True),
    # ---------------------------------------------------------------- country
    "country/train": g("Country: chug stoppato a ottavi sul train beat (boom-chicka-boom alla Johnny Cash)", "twang",
                       pat("BxXxFxXx", 102, 70), TRAIN_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="rootfifth",
                       slap=True, mute_len=0.3, voicing="open"),
    "country/twostep": g("Two-step: basso alternato, chop e pennata in su, un filo di swing", "twang",
                         pat("BnXuFnXu", 100, 58), COUNTRY_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="rootfifth",
                         swing=0.3, voicing="open"),
    "country/ballad": g("Country ballad: accordi aperti lunghi e pennate leggere", "clean",
                        pat("D--uD-du", 95, 55), BALLAD_BEAT, BALLAD_TURN, BALLAD_FILL, bass="slow", voicing="open"),
    "country/bluegrass": g("Bluegrass: pollice alternato e pennate veloci, batteria appena accennata", "clean",
                           pat("BuXuFuXu", 100, 62), BLUEGRASS_BEAT, BRUSH_TURN, SHUFFLE_FILL, bass="rootfifth",
                           voicing="open"),
    "country/outlaw": g("Outlaw country: pennate stoppate a ottavi (stile Waylon Jennings)", "twang",
                        pat("MmMmMmMm", 102, 72), COUNTRY_BEAT, TRAIN_TURN, SHUFFLE_FILL, swing=0.2),
    "country/rock": g("Country rock: basso sul primo e accordi aperti in crunch, chitarre doppiate", "crunch",
                      pat("B.DU.UDU", 105, 75), ROCK_BEAT, bass="rootfifth", double=True, voicing="open"),
    "country/cajun": g("Cajun / two-beat: tonica e quinta in battere, accordo forte in levare", "twang",
                       pat("bUfUbUfU", 95, 70), CAJUN_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="rootfifth",
                       voicing="open"),
    "country/travis": g("Travis picking: pollice alternato e cantini stoppati in levare", "clean",
                        pat("BnFnBnFn", 95, 55), BLUEGRASS_BEAT, BRUSH_TURN, SHUFFLE_FILL, bass="rootfifth",
                        voicing="open"),
    "country/pop": g("Country pop: accordi aperti a sedicesimi, crunch leggero, doppiate", "crunch",
                     pat("D-d-DuDud-d-DuDu", 100, 70), ROCK_BEAT, double=True, voicing="open"),
    "country/western": g("Western swing: comping in quarti con voicing jazz (stile Bob Wills)", "clean",
                         [(b, "J", 90 if b % 2 else 80, 0.5) for b in range(4)], JUMP_BEAT, bass="two", swing=1,
                         **JZ),
    "country/gallop": g("Cowboy gallop: pennate stoppate al galoppo sui tom (stile Ghost Riders)", "twang",
                        pat("M.mmM.mmM.mmM.mm", 102, 72), COWBOY_BEAT, DIDDLEY_TURN, ROCK_FILL),
    "country/brush": g("Country lento a spazzole: basso, chop e levare stoppato", "clean",
                       pat("B.XnF.Xn", 92, 55), BRUSH_BEAT, BRUSH_TURN, SHUFFLE_FILL, bass="rootfifth", swing=0.5,
                       voicing="open"),
    "country/chickin": g("Chicken pickin': chop stoppati a sedicesimi con accenti, slapback", "twang",
                         pat("XxxXxxXxXxxXxxXx", 100, 62), COUNTRY_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="rootfifth",
                         slap=True),
    "country/boogie": g("Country boogie: boogie 5-6 su batteria country (anni '50)", "twang",
                        boogie("55665566", 98), COUNTRY_BEAT, TRAIN_TURN, SHUFFLE_FILL, bass="walk", swing=0.5,
                        mute_len=0.35),
    "country/stomp": g("Country stomp: accordi aperti in quarti, cassa in quattro e rullante pieno", "crunch",
                       pat("D-D-D-D-", 105), STOMP_BEAT, bass="quarters", voicing="open"),
    # ---------------------------------------------------------------- jazz
    "jazz/two": g("Jazz swing in due: basso su 1 e 3, comping alla Freddie Green (temi, intro)", "clean",
                  [(b, "J", 86 if b % 2 == 0 else 76, 0.55) for b in range(4)], JAZZ_BEAT, bass="two", swing=1,
                  voicing="jazz", **JZ),
    "jazz/latin": g("Latin jazz: accordi sulla clave, campana e cassa anticipata, basso tumbao", "clean",
                    pat("J..j..J...j.J...", 90, 75, dur=0.4), LATINJ_BEAT, bass="tumbao", voicing="jazz", **LT_),
    "jazz/samba": g("Samba: accordi sincopati, surdo e hi-hat a sedicesimi", "clean",
                    pat("J..J..J.J..J..J.", 88, 75, dur=0.3), SAMBA_BEAT, bass="rootfifth", voicing="jazz", **LT_),
    "jazz/fast": g("Bebop veloce: comping rado e corto (1, 2&, 3&), ride e bombe sul rullante", "clean",
                   pat("J..j.j..", 88, 74, dur=0.35), FAST_BEAT, bass="walk", swing=1, voicing="jazz", **JZ),
    "jazz/brushes": g("Jazz a spazzole: comping in quarti morbido e walking", "clean",
                      [(b, "J", 78 if b % 2 == 0 else 70, 0.55) for b in range(4)], BRUSH_BEAT, BRUSH_TURN,
                      BRUSH_TURN, bass="walk", swing=1, voicing="jazz"),
    "jazz/afro": g("Afro-cubano 6/8: campana a 12, accordi sulle terzine, basso in due", "clean",
                   pat("J.jJ.jJ.jJ.j", 88, 72, dur=0.3), AFRO_BEAT, bass="two", voicing="jazz", **LT_),
    "jazz/basie": g("Jazz shuffle alla Count Basie: quarti di chitarra, rullante su 2 e 4", "clean",
                    [(b, "J", 88 if b % 2 else 80, 0.5) for b in range(4)], JUMP_BEAT, bass="walk", swing=1,
                    voicing="jazz", **JZ),
    "jazz/modal": g("Jazz modale: due accordi in levare lasciati suonare (stile So What)", "clean",
                    pat("...J-..J", 85), JAZZ_BEAT, bass="walk", swing=1, voicing="jazz", **JZ),
    "jazz/funk": g("Soul jazz / jazz funk: accordi corti a sedicesimi, batteria funk", "clean",
                   pat("J..j..J...j..J..", 90, 75, dur=0.25), FUNK_BEAT, FUNK_TURN, bass="funk", voicing="jazz"),
    "jazz/gypsy": g("Jazz manouche: la pompe, basso corto su 1 e 3 e chop forte su 2 e 4", "clean",
                    pat("j.X.j.X.", 102, 72, dur=0.3), BRUSH_BEAT, BRUSH_TURN, BRUSH_TURN, bass="two", swing=1,
                    voicing="jazz"),
    "jazz/cha": g("Cha-cha-chà: accordi su 1-2-3 e 4&, campana in quarti e basso tumbao", "clean",
                  pat("J.J.J.jj", 88, 78, dur=0.35), CHA_BEAT, bass="tumbao", voicing="jazz", **LT_),
    # ---------------------------------------------------------------- funk
    "funk": g("Funk: pennate a sedicesimi con chop stoppati, accenti sul levare (stile James Brown)", "clean",
              pat("DxxUxxDxxxDxxUxx", 100, 62, dur=0.2), FUNK_BEAT, FUNK_TURN, bass="funk", voicing="triad"),
    "funk/disco": g("Disco funk: cassa in quattro, hi-hat aperto in levare, sedicesimi (stile Nile Rodgers)", "clean",
                    pat("dudUdudUdudUdudU", 92, 70, dur=0.22), DISCO_BEAT, FUNK_TURN, bass="octave", double=True,
                    voicing="triad"),
    "funk/scratch": g("Chicken scratch: solo chop stoppati a sedicesimi con accenti", "clean",
                      pat("XxxXxxXxXxxXxxXx", 100, 60), FUNK_BEAT, FUNK_TURN, bass="funk", voicing="triad"),
    "funk/one": g("Funk 'on the one': accordo lungo sul primo, chop sparsi dopo", "clean",
                  pat("D-.....x...X..X.", 110, 70), FUNK2_BEAT, FUNK_TURN, bass="funk", voicing="triad"),
    "funk/clav": g("Funk clavinet: stab jazz a sedicesimi sincopati (stile Superstition)", "clean",
                   pat("J.jJ..j.J.jJ..jJ", 95, 72, dur=0.2), FUNK_BEAT, FUNK_TURN, bass="funk", voicing="jazz"),
    "funk/slow": g("Slow funk: accordo lungo e chop, rullante sul 3", "clean",
                   pat("D---..xX..x...X.", 100, 65), SLOWFUNK_BEAT, HALFTIME_TURN, bass="funk", voicing="triad"),
    "funk/purdie": g("Funk shuffle alla Purdie: half-time con ghost note, chop swingati", "clean",
                     pat("DxXxDxXx", 100, 62), PURDIE_BEAT, SHUFFLE_TURN, SHUFFLE_FILL, bass="walk", swing=0.6,
                     voicing="triad"),
    "funk/pocket": g("Funk in pocket: accordi corti sincopati e chop", "clean",
                     pat("D..x..Dx.xD..xD.", 100, 62, dur=0.25), FUNK2_BEAT, FUNK_TURN, bass="funk", voicing="triad"),
    "funk/gogo": g("Go-go di Washington: chop swingati, campana e cassa sincopata", "clean",
                   pat("X.x.X..xX.x.X..x", 100, 65), GOGO_BEAT, FUNK_TURN, bass="funk", swing=0.6, voicing="triad"),
    "funk/rock": g("Funk rock: power chord sincopati in crunch, doppiate", "crunch",
                   pat("P..P..P.P.p.P..p", 110, 85), FUNK_BEAT, FUNK_TURN, bass="funk", double=True),
    "funk/boogaloo": g("Boogaloo: tonica e quinta sincopate come una linea di basso (stile Cissy Strut)", "clean",
                       pat("B..b..F.B.b...f.", 100, 75, dur=0.3), BOOGALOO_BEAT, FUNK_TURN, bass="funk"),
    "funk/lowrider": g("Latin funk: pennate sincopate, campana in quarti, basso tumbao (stile Low Rider)", "crunch",
                       pat("D.dD..u.D.dD..u.", 100, 70), LOWRIDER_BEAT, LATIN_TURN, bass="tumbao", voicing="open"),
    "funk/fusion": g("Fusion: accordi jazz 3-3-2 lasciati suonare, basso in ottave", "clean",
                     pat("J--j--J-J--j--J-", 88, 72), FUNK2_BEAT, FUNK_TURN, bass="octave", voicing="jazz"),
    "funk/pop": g("Pop funk anni '80: chop radi in levare, hi-hat a sedicesimi (stile Prince)", "clean",
                  pat("..X..xX...X..xX.", 100, 65), POP_BEAT, FUNK_TURN, bass="funk", voicing="triad"),
    "funk/halftime": g("Funk half-time: accordo sul primo e chop a sedicesimi, rullante sul 3", "clean",
                       pat("D-xxX-xxD-xxX-xx", 100, 58), SLOWFUNK_BEAT, HALFTIME_TURN, bass="funk", voicing="triad"),
    # ---------------------------------------------------------------- reggae
    "reggae": g("Reggae one drop: skank corto sul 2 e 4, cassa sul 3, basso lento", "clean",
                [(1, "C", 100), (3, "C", 100)], ONEDROP_BEAT, bass="reggae", swing=0.3, voicing="triad", **OD),
    "reggae/ska": g("Ska: pennate in su stoppate su tutti i levare, hi-hat aperto, ritmo veloce", "clean",
                    [(b + 0.5, "Um", 100, 0.2) for b in range(4)], SKA_BEAT, bass="walk", voicing="triad"),
    "reggae/rockers": g("Rockers: skank doppio sul 2 e 4, cassa su 1 e 3 (anni '70)", "clean",
                        pat("....Xx......Xx..", 100, 70), ROCKERS_BEAT, bass="reggae", swing=0.2, voicing="triad",
                        **OD),
    "reggae/steppers": g("Steppers: cassa in quattro, skank su ogni levare", "clean",
                         pat("..X...X...X...X.", 95), STEPPERS_BEAT, swing=0.2, voicing="triad", **OD),
    "reggae/bubble": g("Bubble: chop a sedicesimi come l'organo reggae, one drop", "clean",
                       pat(".xX..xX..xX..xX.", 95, 60), ONEDROP_BEAT, bass="reggae", swing=0.3, voicing="triad",
                       **OD),
    "reggae/rocksteady": g("Rocksteady: skank sul 2 e 4 con levare stoppato, basso che cammina", "clean",
                           pat("....X.n.....X.n.", 100, 55), ONEDROP_BEAT, bass="walk", swing=0.5, voicing="triad",
                           **OD),
    "reggae/dub": g("Dub: un solo skank sul 2, tanto spazio, basso in due", "clean",
                    [(1, "C", 100)], ONEDROP_BEAT, bass="two", swing=0.3, voicing="triad", **OD),
    "reggae/dancehall": g("Dancehall: ritmo dembow, chop in levare", "clean",
                          pat("..x...x...x...x.", 95, 80), DEMBOW_BEAT, bass="dotted", voicing="triad", **OD),
    "reggae/roots": g("Roots reggae: skank sul 2 e 4 ripetuto in levare", "clean",
                      pat("....X.X.....X.X.", 100, 70), ONEDROP_BEAT, bass="reggae", swing=0.3, voicing="triad",
                      **OD),
    "reggae/lovers": g("Lovers rock: accordo aperto lungo e skank sul 4", "clean",
                       pat("D---X-......X...", 90), ONEDROP_BEAT, bass="slow", swing=0.3, voicing="open", **OD),
    "reggae/skinhead": g("Early reggae: doppie pennate stoppate in levare, veloce", "clean",
                         pat("..Nn..Nn..Nn..Nn", 100, 65), SKA_BEAT, bass="walk", voicing="triad"),
    "reggae/calypso": g("Calypso / soca: pennate sincopate aperte, cassa in quattro", "clean",
                        pat("D..D..DUD..D..DU", 100, 70), CALYPSO_BEAT, LATIN_TURN, bass="dotted", voicing="open"),
    "reggae/2tone": g("Ska 2-tone: levare stoppati in crunch, batteria punk", "crunch",
                      pat(".N.N.N.N", 105), PUNK_BEAT, bass="walk", voicing="triad"),
    "reggae/police": g("Rock reggae: accordi lunghi sui levare, one drop dritto (stile The Police)", "clean",
                       pat("..D-....D-...D--", 95), ONEDROP8_BEAT, bass="two", voicing="triad", **OD),
    "reggae/bluebeat": g("Blue beat: ska in shuffle, levare stoppati swingati", "clean",
                         pat(".N.N.N.N", 100), SKA_BEAT, bass="walk", swing=1, voicing="triad", **SH),
    # ---------------------------------------------------------------- soul
    "soul": g("Soul / Motown: chop sul 2 e 4, rullante su tutti i tempi", "clean",
              [(1, "C", 100), (3, "C", 100), (3.5, "Um", 55)], MOTOWN_BEAT, voicing="triad"),
    "soul/ballad": g("Soul ballad 12/8 (doo-wop): accordi sulle terzine, ride, basso lento", "clean",
                     pat("DuuDuuDuuDuu", 85, 55), DOOWOP_BEAT, SLOW_TURN, SLOW_FILL, bass="slow", voicing="open"),
    "soul/memphis": g("Memphis soul (Stax): stab corti sul 2 e 4 (stile Steve Cropper)", "clean",
                      pat("....X..x....X...", 102, 65), MEMPHIS_BEAT, bass="dotted", voicing="triad"),
    "soul/gospel": g("Gospel 12/8: accordo lungo e chop sulle terzine, ride", "clean",
                     pat("D--X--D--X--", 100), SLOW_BEAT, SLOW_TURN, SLOW_FILL, bass="slow", voicing="open"),
    "soul/northern": g("Northern soul: cassa in quattro, rullante su tutti i tempi, uptempo", "clean",
                       pat("D.X.D.X.", 100), NORTHERN_BEAT, voicing="triad"),
    "soul/philly": g("Philly soul: chop a sedicesimi, hi-hat aperto in levare, basso in ottave", "clean",
                     pat("xXxXxXxXxXxXxXxX", 92, 60), PHILLY_BEAT, FUNK_TURN, bass="octave", double=True,
                     voicing="triad"),
    "soul/neo": g("Neo soul: accordi jazz lunghi e laid-back, rim su 2 e 4", "clean",
                  pat("J--..j-.J-...j..", 85, 70), NEO_BEAT, FUNK_TURN, bass="dotted", swing=0.6, voicing="jazz"),
    "soul/rnb": g("R&B anni '50: ottavi dritti sul ritmo latino, basso tumbao (stile What'd I Say)", "clean",
                  pat("DdDdDdDd", 95, 70), RHUMBA_BEAT, RHUMBA_TURN, SHUFFLE_FILL, bass="tumbao", voicing="triad"),
    "soul/funky": g("Soul funky: accordi sincopati e chop (stile Sly Stone)", "clean",
                    pat("D..D..d.D.x..x..", 100, 68, dur=0.3), FUNK_BEAT, FUNK_TURN, bass="funk", voicing="triad"),
    "soul/spector": g("Wall of sound: ottavi aperti, boom . boom-boom CHA (stile Be My Baby)", "clean",
                      pat("DuDuDuDu", 100, 70), SPECTOR_BEAT, bass="dotted", double=True, voicing="open"),
    "soul/swamp": g("Swamp soul: pennate stoppate swingate (stile Tony Joe White)", "twang",
                    pat("Mm.mMm.m", 100, 70), SHUFFLE_BEAT, bass="walk", swing=0.6, **SH),
    "soul/blues": g("Soul blues: accordo lungo e chop, batteria half-time (stile Al Green)", "clean",
                    pat("D---..X.D-....X.", 95, 65), BALLAD_BEAT, BALLAD_TURN, BALLAD_FILL, bass="slow",
                    voicing="triad"),
    "soul/sweet": g("Sweet soul: accordi aperti e pennate leggere in su", "clean",
                    pat("D-uuD-uu", 90, 55), BALLAD_BEAT, BALLAD_TURN, BALLAD_FILL, bass="slow", voicing="open"),
    "soul/sixeight": g("Soul 6/8: accordi jazz sulle terzine, basso in due", "clean",
                       pat("JjjJjjJjjJjj", 85, 58), DOOWOP_BEAT, SLOW_TURN, SLOW_FILL, bass="two", voicing="jazz"),
    "soul/boogaloo": g("Soul boogaloo: chop sincopati e cassa a sedicesimi", "clean",
                       pat("X..x..X...x.X...", 100, 65), BOOGALOO_BEAT, FUNK_TURN, bass="funk", swing=0.2,
                       voicing="triad"),
})


def get_groove(name):
    if name not in GROOVES:
        raise SongError("groove sconosciuto '%s'. Disponibili: %s" % (name, ", ".join(GROOVES)))
    return GROOVES[name]
