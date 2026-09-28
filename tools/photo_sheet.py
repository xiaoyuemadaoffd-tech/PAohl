# -*- coding: utf-8 -*-
"""把 images 下的候选照片拼成一张带标签的联系表，方便挑选摄影作品。

用法: python photo_sheet.py 输出文件名.jpg 图片1 图片2 ...
输出: tools/<输出文件名>.jpg
"""
import os
import sys

import pymupdf
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 2026年投递
OUTDIR = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) < 3:
    raise SystemExit("用法: python photo_sheet.py 输出名.jpg img1 img2 ...")

out = os.path.join(OUTDIR, sys.argv[1])
names = sys.argv[2:]

THUMB, GAP, LABEL_H = 200, 10, 16
COLS = 5
rows = (len(names) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * (THUMB + GAP) + GAP,
                          rows * (THUMB + LABEL_H + GAP) + GAP), "white")
draw = ImageDraw.Draw(sheet)

for i, name in enumerate(names):
    # 绝对路径直接用；否则视为 images/ 下的文件名
    path = name if os.path.isabs(name) else os.path.join(BASE, "images", name)
    if not os.path.exists(path):
        print("缺失:", path)
        continue
    pix = pymupdf.Pixmap(path)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im.thumbnail((THUMB, THUMB), Image.LANCZOS)
    x = GAP + (i % COLS) * (THUMB + GAP)
    y = GAP + (i // COLS) * (THUMB + LABEL_H + GAP)
    sheet.paste(im, (x, y))
    draw.rectangle([x - 1, y - 1, x + THUMB, y + THUMB], outline=(210, 210, 210))
    draw.text((x, y + THUMB + 2), "%d) %s  %dx%d" % (i + 1, name, pix.width, pix.height),
              fill=(0, 0, 0))

sheet.save(out, "JPEG", quality=88)
print(out, sheet.size)
