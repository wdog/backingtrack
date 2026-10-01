"""Genera docs/logo.jpg e docs/pipeline.jpg (serve Pillow): python docs/make_images.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FC = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
S = 2
W, H = 1600*S, 520*S
AMBER, CREAM, RED, DARK = (245,166,35), (243,233,210), (192,57,43), (24,22,22)

img = Image.new("RGB", (W, H), DARK)
d = ImageDraw.Draw(img)
# tolex/grille: trama diagonale
for x in range(-H, W, 14*S):
    d.line([(x,0),(x+H,H)], fill=(34,31,30), width=3*S)
    d.line([(x+H,0),(x,H)], fill=(30,28,27), width=2*S)
# vignetta
v = Image.new("L", (W,H), 0); vd = ImageDraw.Draw(v)
vd.ellipse([-W*0.2,-H*0.6,W*1.2,H*1.6], fill=255)
v = v.filter(ImageFilter.GaussianBlur(120*S))
img = Image.composite(img, Image.new("RGB",(W,H),(10,9,9)), v)
d = ImageDraw.Draw(img)
# bordo stile ampli
d.rounded_rectangle([18*S,18*S,W-18*S,H-18*S], radius=36*S, outline=(70,62,55), width=6*S)
d.rounded_rectangle([30*S,30*S,W-30*S,H-30*S], radius=28*S, outline=AMBER, width=2*S)

# plettro
cx, cy, r = 300*S, 250*S, 170*S
pts = []
for i in range(360):
    a = math.radians(i)
    # plettro: cerchio deformato verso il basso
    k = 1 + 0.55*max(0, math.sin(a))**3
    pts.append((cx + r*0.92*math.cos(a), cy - 30*S + r*k*math.sin(a)*0.95))
shadow = Image.new("L",(W,H),0); ImageDraw.Draw(shadow).polygon([(x+10*S,y+14*S) for x,y in pts], fill=200)
img.paste((0,0,0), mask=shadow.filter(ImageFilter.GaussianBlur(18*S)))
grad = Image.new("RGB",(W,H))
gd = ImageDraw.Draw(grad)
for y in range(H):
    t = y/H
    gd.line([(0,y),(W,y)], fill=(int(250-40*t), int(180-90*t), int(40+10*t)))
mask = Image.new("L",(W,H),0); ImageDraw.Draw(mask).polygon(pts, fill=255)
img.paste(grad, mask=mask)
d = ImageDraw.Draw(img)
d.polygon(pts, outline=(255,220,150), width=3*S)
# forma d'onda / equalizzatore nel plettro
bars = [0.25,0.45,0.8,0.55,1.0,0.7,0.4,0.9,0.5,0.3]
bw = 18*S; gap = 9*S
x0 = cx - (len(bars)*(bw+gap)-gap)/2
for i,b in enumerate(bars):
    h = b*150*S
    x = x0 + i*(bw+gap)
    d.rounded_rectangle([x, cy-10*S-h/2, x+bw, cy-10*S+h/2], radius=bw/2, fill=DARK)

# testo
f1 = ImageFont.truetype(FB, 132*S)
f2 = ImageFont.truetype(FC, 38*S)
f3 = ImageFont.truetype(FR, 30*S)
tx = 560*S
d.text((tx+5*S, 90*S+6*S), "backing", font=f1, fill=(0,0,0))
d.text((tx, 90*S), "backing", font=f1, fill=CREAM)
wb = d.textlength("backing", font=f1)
d.text((tx+wb+5*S, 90*S+6*S), "track", font=f1, fill=(0,0,0))
d.text((tx+wb, 90*S), "track", font=f1, fill=AMBER)
# stili su due righe (tutti quelli dei groove)
for i, row in enumerate(["ROCK  ·  BLUES  ·  ROCKABILLY  ·  COUNTRY", "JAZZ  ·  FUNK  ·  REGGAE  ·  SOUL"]):
    d.text((tx+4*S, (272+50*i)*S), row, font=f2, fill=CREAM if i == 0 else AMBER)
d.line([(tx+4*S, 385*S), (tx+900*S, 385*S)], fill=RED, width=4*S)
d.text((tx+4*S, 402*S), "chitarra e batteria vere, dai tuoi accordi", font=f3, fill=(200,190,170))

img.resize((W//S, H//S), Image.LANCZOS).save(Path(__file__).parent / "logo.jpg", quality=92)

# -------- diagramma pipeline
W, H = 1800*S, 560*S
img = Image.new("RGB",(W,H),(250,247,240)); d = ImageDraw.Draw(img)
ft = ImageFont.truetype(FB, 34*S); fs = ImageFont.truetype(FR, 23*S); fh = ImageFont.truetype(FB, 40*S)
d.text((60*S,36*S), "Come funziona", font=fh, fill=DARK)
boxes = [
 ("song.yaml", ["tempo, groove", "sezioni e accordi", "ripetizioni"], (90,90,90)),
 ("Arranger", ["accordi → note", "pennate, swing, fill", "umanizzazione"], (192,57,43)),
 ("Sampler", ["numpy + SFZ", "chitarra Gretsch", "batteria Salamander"], (214,120,20)),
 ("Mixer", ["ffmpeg: ampli, cassa IR", "EQ, comp, riverbero", "slapback, limiter"], (40,110,150)),
 ("Output", ["WAV · MP3", "MIDI per la DAW", "stems separati"], (60,130,70)),
]
bw, bh, y = 300*S, 300*S, 150*S
gap = (W - 120*S - len(boxes)*bw) / (len(boxes)-1)
for i,(title, lines, col) in enumerate(boxes):
    x = 60*S + i*(bw+gap)
    d.rounded_rectangle([x+6*S,y+8*S,x+bw+6*S,y+bh+8*S], radius=26*S, fill=(220,214,202))
    d.rounded_rectangle([x,y,x+bw,y+bh], radius=26*S, fill="white", outline=col, width=5*S)
    d.rounded_rectangle([x,y,x+bw,y+78*S], radius=26*S, fill=col)
    d.rectangle([x,y+50*S,x+bw,y+78*S], fill=col)
    tw = d.textlength(title, font=ft)
    d.text((x+(bw-tw)/2, y+18*S), title, font=ft, fill="white")
    for j,l in enumerate(lines):
        lw = d.textlength(l, font=fs)
        d.text((x+(bw-lw)/2, y+112*S+j*52*S), l, font=fs, fill=(50,50,50))
    if i < len(boxes)-1:
        ax, ay = x+bw+14*S, y+bh/2
        d.line([(ax,ay),(ax+gap-28*S,ay)], fill=(120,110,100), width=6*S)
        d.polygon([(ax+gap-28*S,ay-16*S),(ax+gap-8*S,ay),(ax+gap-28*S,ay+16*S)], fill=(120,110,100))
img.resize((W//S,H//S), Image.LANCZOS).save(Path(__file__).parent / "pipeline.jpg", quality=92)
print("ok")

# -------- icona dell'app (plettro), 256x256 PNG
S2 = 4
W = H = 256 * S2
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cx, cy, r = W / 2, H / 2 + 4 * S2, 104 * S2
pts = []
for i in range(360):
    a = math.radians(i)
    k = 1 + 0.55 * max(0, math.sin(a)) ** 3
    pts.append((cx + r * 0.9 * math.cos(a), cy - 18 * S2 + r * k * math.sin(a) * 0.93))
grad = Image.new("RGBA", (W, H))
gd = ImageDraw.Draw(grad)
for y in range(H):
    t = y / H
    gd.line([(0, y), (W, y)], fill=(int(250 - 40 * t), int(180 - 90 * t), int(40 + 10 * t), 255))
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).polygon(pts, fill=255)
img.paste(grad, mask=mask)
d = ImageDraw.Draw(img)
d.polygon(pts, outline=(255, 225, 160, 255), width=5 * S2)
bars = [0.35, 0.6, 1.0, 0.7, 0.9, 0.5, 0.3]
bw, gap = 16 * S2, 8 * S2
x0 = cx - (len(bars) * (bw + gap) - gap) / 2
for i, b in enumerate(bars):
    h = b * 110 * S2
    x = x0 + i * (bw + gap)
    d.rounded_rectangle([x, cy - 12 * S2 - h / 2, x + bw, cy - 12 * S2 + h / 2], radius=bw / 2, fill=(28, 24, 24, 255))
icon = img.resize((256, 256), Image.LANCZOS)
icon.save(Path(__file__).parent.parent / "backingtrack" / "data" / "io.github.wdog.backingtrack.png")
print("icona ok")
