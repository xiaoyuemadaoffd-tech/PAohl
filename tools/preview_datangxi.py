# -*- coding: utf-8 -*-
"""把 PDF 指定页范围渲染成缩略拼版，用于人工确认页码与裁切效果。

用法: python preview_datangxi.py [起始页] [结束页] [每行张数]
输出: tools/preview_sheet.jpg
"""
import os
import sys

import pymupdf
from PIL import Image, ImageDraw

PDF = r"E:\4.实习\简历\2026年投递\书籍设计\大唐以西.pdf"
FIRST = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST = int(sys.argv[2]) if len(sys.argv) > 2 else 20
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
THUMB_W = 260
GAP, LABEL_H = 10, 16
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_sheet.jpg")

doc = pymupdf.open(PDF)
thumbs = []
for no in range(FIRST, LAST + 1):
    page = doc[no - 1]
    # clip=trimbox：裁掉裁切线与出血区，只留成品页面
    pix = page.get_pixmap(clip=page.trimbox, matrix=pymupdf.Matrix(0.6, 0.6), alpha=False)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im = im.resize((THUMB_W, round(im.height * THUMB_W / im.width)), Image.LANCZOS)
    thumbs.append((no, im))
doc.close()

tw, th = thumbs[0][1].size
rows = (len(thumbs) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * (tw + GAP) + GAP,
                          rows * (th + LABEL_H + GAP) + GAP), "white")
draw = ImageDraw.Draw(sheet)
for i, (no, im) in enumerate(thumbs):
    x = GAP + (i % COLS) * (tw + GAP)
    y = GAP + (i // COLS) * (th + LABEL_H + GAP)
    sheet.paste(im, (x, y))
    draw.rectangle([x - 1, y - 1, x + tw, y + th], outline=(200, 200, 200))
    draw.text((x, y + th + 2), "PDF p%d" % no, fill=(0, 0, 0))

sheet.save(OUT, "JPEG", quality=88)
print("拼版:", len(thumbs), "页 ->", OUT, os.path.getsize(OUT) // 1024, "KB")
