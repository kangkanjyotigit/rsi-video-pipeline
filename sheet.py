"""Build a contact sheet from a video: sheet.py <video> <out.jpg> <t1> <t2> ... [--cols N]"""
import subprocess, sys, os
from PIL import Image, ImageDraw

def main():
    args = sys.argv[1:]
    cols = 3
    if "--cols" in args:
        i = args.index("--cols"); cols = int(args[i+1]); del args[i:i+2]
    video, out = args[0], args[1]
    times = [float(x) for x in args[2:]]
    W = 640
    tiles = []
    for t in times:
        tmp = f"_sh_{t}.png"
        subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",video,
                        "-frames:v","1","-vf",f"scale={W}:-1",tmp], check=True)
        im = Image.open(tmp).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle([0,0,74,20], fill=(0,0,0))
        d.text((5,4), f"{t:g}s", fill=(255,220,80))
        tiles.append(im); os.remove(tmp)
    rows = (len(tiles)+cols-1)//cols
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (tw*cols, th*rows), (10,10,16))
    for i,im in enumerate(tiles):
        sheet.paste(im, ((i%cols)*tw, (i//cols)*th))
    sheet.save(out, quality=88)
    print(f"{out}: {sheet.size[0]}x{sheet.size[1]} ({len(tiles)} frames)")

main()
