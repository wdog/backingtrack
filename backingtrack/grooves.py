"""Groove: pattern di chitarra e batteria per una battuta di 4/4.

Evento chitarra: (beat, tipo, velocity[, durata in beat])
  D  pennata giù (tutte le corde)       U  pennata su (4 corde alte)
  C  chop: 4 corde alte stoppate        P  power chord
  B / B5  nota di basso: tonica / quinta
  R5 R6 R7  bicordi boogie (tonica + 5a / 6a / 7a minore)
  suffisso "m" = stoppato (palm mute)

Evento batteria: (beat, nota GM, velocity). I beat in levare (.5) vengono spostati dallo swing.
"""
from .errors import SongError

# GM drum map (usato anche per l'export MIDI)
KICK, STICK, SNARE, HH, PEDAL, OHH = 36, 37, 38, 42, 44, 46
LT, MT, HT, CRASH, RIDE = 45, 47, 50, 49, 51

T1, T2 = 1 / 3, 2 / 3


def hat8(on=90, off=60, note=HH):
    return [(i / 2, note, on if i % 2 == 0 else off) for i in range(8)]


def boogie(pattern, vel=95):
    kinds = {"5": "R5m", "6": "R6m", "7": "R7m"}
    return [(i / 2, kinds[c], vel if i % 2 == 0 else vel - 15) for i, c in enumerate(pattern)]


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
STOP_BEAT = [(0, KICK, 118), (0, SNARE, 90), (0, CRASH, 90), (1, HH, 45), (2, HH, 45), (3, HH, 45)]
COUNTRY_BEAT = ([(0, KICK, 95), (2, KICK, 90), (1, SNARE, 100), (3, SNARE, 100)] +
                [(i / 2, SNARE, 30) for i in (1, 3, 5, 7)] + hat8(70, 45, PEDAL))

STRUM_DDU = [(0, "D", 110), (1, "D", 95), (1.5, "U", 75), (2.5, "U", 80), (3, "D", 95), (3.5, "U", 75)]

# amp: clean | blues | twang | crunch | high     double: chitarra doppiata L/R
GROOVES = {
    "rock": dict(
        desc="Rock: power chord a ottavi con palm mute, ampli distorto, chitarre doppiate",
        amp="high", double=True, swing=0, bass_style="eighths",
        guitar=[(0, "P", 118, 0.5)] + [(i / 2, "Pm", 88 if i % 2 else 102) for i in range(1, 8)],
        drums=ROCK_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "rock/strum": dict(
        desc="Rock: accordi aperti D . D U . U D U, crunch, chitarre doppiate",
        amp="crunch", double=True, swing=0, bass_style="eighths",
        guitar=STRUM_DDU, drums=ROCK_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "rock/drive": dict(
        desc="Rock: pennate giù a ottavi, accordi pieni (punk/drive)",
        amp="crunch", double=True, swing=0, bass_style="eighths",
        guitar=[(i / 2, "D", 105 if i % 2 == 0 else 88) for i in range(8)],
        drums=ROCK_BEAT, turn=ROCK_TURN, fill=ROCK_FILL),
    "rock/ballad": dict(
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
        desc="Country: boom-chick dritto, basso alternato e spazzolata sul 2 e 4",
        amp="twang", double=False, swing=0, bass_style="rootfifth",
        guitar=[(0, "B", 100), (1, "C", 95), (2, "B5", 98), (3, "C", 95), (3.5, "Um", 55)],
        drums=COUNTRY_BEAT, turn=TRAIN_TURN, fill=SHUFFLE_FILL),
    "country/shuffle": dict(
        desc="Country shuffle: boom-chick in swing, stile Texas / honky-tonk",
        amp="twang", double=False, swing=0.7, bass_style="walk",
        guitar=[(0, "B", 100), (1, "C", 95), (1.5, "Um", 55), (2, "B5", 98), (3, "C", 95), (3.5, "Um", 55)],
        drums=SHUFFLE_BEAT, turn=SHUFFLE_TURN, fill=SHUFFLE_FILL),
}


def get_groove(name):
    if name not in GROOVES:
        raise SongError("groove sconosciuto '%s'. Disponibili: %s" % (name, ", ".join(GROOVES)))
    return GROOVES[name]
