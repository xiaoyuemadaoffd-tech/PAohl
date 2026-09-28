# -*- coding: utf-8 -*-
"""把选中的个人摄影作品整理成侧栏 3x3 网格用的图片。

统一缩到宽度 900px（缩略图 70px、灯箱约 860px，都够用），
输出到 images/photo/01.jpg ... 09.jpg，方便页面统一引用。

用法: python make_photo_grid.py

注意：源图里 zuibaichi*.jpg 还在 images/，children.jpg 已归档到
E:\4.实习\简历\_作品集原图存档\images\，重跑前先拷回来。
"""
import os

import pymupdf
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 2026年投递
SHEYING = r"E:\4.实习\简历\简历与作品集-2023年改\摄影"
OUTDIR = os.path.join(BASE, "images", "photo")

WIDTH = 900
QUALITY = 82

# 顺序即网格里的排列顺序（左到右、上到下）
SOURCES = [
    os.path.join(BASE, "images", "zuibaichi (1).jpg"),   # 园林夜游
    os.path.join(BASE, "images", "zuibaichi (3).jpg"),
    os.path.join(BASE, "images", "zuibaichi (4).jpg"),
    os.path.join(SHEYING, "mmexport1698941445945.jpg"),  # 汉服人像
    os.path.join(SHEYING, "mmexport1698941462810.jpg"),
    os.path.join(SHEYING, "mmexport1698941464940.jpg"),
    os.path.join(SHEYING, "mmexport1698941468545.jpg"),
    os.path.join(SHEYING, "mmexport1698941545827.jpg"),
    os.path.join(BASE, "images", "children.jpg"),        # 展陈纪实
]

os.makedirs(OUTDIR, exist_ok=True)
total = 0
for i, src in enumerate(SOURCES):
    if not os.path.exists(src):
        print("缺失:", src)
        continue
    pix = pymupdf.Pixmap(src)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if im.width > WIDTH:
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
    out = os.path.join(OUTDIR, "%02d.jpg" % (i + 1))
    im.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    size = os.path.getsize(out)
    total += size
    print("%02d  %-42s %d x %d  %d KB" % (i + 1, os.path.basename(src), im.width, im.height, size // 1024))

print("合计 %.1f MB -> %s" % (total / 1048576, OUTDIR))
