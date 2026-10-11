"""Full-resolution edge band crops, stacked for inspection.

Usage: edgecrop.py <video> <out.jpg> <L|R|T|B> <t1> [t2 ...] [--band N]
"""
import subprocess, sys, os
from PIL import Image, ImageDraw

args = sys.argv[1:]
band = 360
if "--band" in args:
    i = args.index("--band"); band = int(args[i+1]); del args[i:i+2]
video, out, edge = args[0], args[1], args[2].upper()
times = [float(x) for x in args[3:]]
W, H = 1920, 1080

tiles, tmp = [], "_ec.png"
for t in times:
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",video,
                    "-frames:v","1","-pix_fmt","rgb24",tmp], check=True)
    im = Image.open(tmp).convert("RGB")
    box = {"L":(0,0,band,H), "R":(W-band,0,W,H),
           "T":(0,0,W,band), "B":(0,H-band,W,H)}[edge]
    c = im.crop(box)
    d = ImageDraw.Draw(c)
    d.rectangle([0,0,116,22], fill=(0,0,0))
    d.text((6,5), f"{t:g}s {edge}", fill=(255,220,80))
    tiles.append(c)
    os.remove(tmp)

tw, th = tiles[0].size
if edge in ("L","R"):
    sheet = Image.new("RGB",(tw*len(tiles)+2*(len(tiles)-1), th),(255,0,0))
    for i,im in enumerate(tiles): sheet.paste(im,(i*(tw+2),0))
else:
    sheet = Image.new("RGB",(tw, th*len(tiles)+2*(len(tiles)-1)),(255,0,0))
    for i,im in enumerate(tiles): sheet.paste(im,(0,i*(th+2)))
sheet.save(out, quality=90)
print(f"{out}: {sheet.size[0]}x{sheet.size[1]}  ({edge} band {band}px @ {times})")
