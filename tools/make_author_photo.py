# -*- coding: utf-8 -*-
"""把 images/author.JPG 按原比例缩成网页用图（不裁切、不改变构图）。

页面里侧栏照片显示宽度约 224px，按 2 倍屏取 640px 足够清晰，
同时把 964KB 的原图压到百来 KB，避免为了一个小图加载大文件。

用法: python make_author_photo.py [宽度] [质量]
输出: images/author-photo.jpg

注意：源图 images/author.JPG 已归档到 E:\4.实习\简历\_作品集原图存档\images\
（作品集要传给 GitHub，只留页面真正引用的图片），重跑前先把原图拷回 images/。
"""
import os
import sys

import pymupdf
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 2026年投递
SRC = os.path.join(BASE, "images", "author.JPG")
OUT = os.path.join(BASE, "images", "author-photo.jpg")

WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 640
QUALITY = int(sys.argv[2]) if len(sys.argv) > 2 else 86

pix = pymupdf.Pixmap(SRC)
im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
if im.width > WIDTH:
    # 等比缩放，保留整张原图（不做任何裁剪）
    im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
im.save(OUT, "JPEG", quality=QUALITY, optimize=True, progressive=True)

print("原图 %d x %d  ->  %s  %d x %d  %d KB"
      % (pix.width, pix.height, OUT, im.width, im.height,
         os.path.getsize(OUT) // 1024))
