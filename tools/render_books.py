# -*- coding: utf-8 -*-
"""把四本展册 PDF 渲染成网页用的逐页 JPG。

用法: python render_books.py
输出: <作品集目录>/images/books/<key>/01.jpg ...

注意：网页实际引用的是合并后的长条拼图 images/sheets/*，所以完整的换图流程是
  1) python render_books.py     # 逐页导出到 images/books/
  2) python make_strips.py      # 合并成 images/sheets/*，并打印要同步到 index.html 的配置
  3) 把 images/books/ 移回 _作品集原图存档/images/（页面不再直接引用逐页图，
     留着会让上传 GitHub 的文件数重新超过 100）
"""
import glob
import os
import re
import shutil
import sys

import pymupdf
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO = os.path.dirname(BASE)          # 2026年投递
OUT_ROOT = os.path.join(PORTFOLIO, "images", "books")

# 目标渲染宽度（页面显示宽度约 400~560px，2 倍图足够清晰）
TARGET_W = 1100
QUALITY = 82
PICTURE_BOOKS = os.path.join(PORTFOLIO, "书籍设计")

# 每本书的 source：("pdf", 文件路径) 或 ("images", 图片文件夹)
# width / quality 可单独覆盖，页数多的书调小一点控制总体积
BOOKS = [
    {
        "key": "picasso",
        "label": "非常毕加索：保罗·史密斯的新视角",
        "source": ("pdf", r"E:\4.实习\艺科画室\毕加索展\毕加索展览导览册.pdf"),
    },
    {
        "key": "qitan",
        "label": "中国奇谭：造梦奇境艺术展",
        "source": ("pdf", r"E:\4.实习\艺科画室\中国奇谭 造梦奇境艺术展.pdf"),
    },
    {
        "key": "gejian",
        "label": "格间漫游：瑞士当代漫画展",
        "source": ("pdf", os.path.join(PICTURE_BOOKS, "美育", "格间漫游.pdf")),
    },
    {
        "key": "bologna",
        "label": "58 届博洛尼亚插画展",
        "source": ("images", os.path.join(PICTURE_BOOKS, "美育", "博洛尼亚插画展导览册 副本")),
    },
    {
        "key": "datangxi",
        "label": "大唐以西",
        "source": ("pdf", os.path.join(PICTURE_BOOKS, "大唐以西.pdf")),
        "trim": True,      # 印刷稿：按 TrimBox 裁掉裁切线与出血区
        # 前 19 页 + 封底（第 70 页）。前 19 页必须从第 1 页起连续截取：
        # 翻页是 (1)(2-3)(4-5)… 成对展示，跳页会让左右跨页整体错位；
        # 封底放在最后单独成屏，收尾才像一本完整的书
        "keep": list(range(1, 20)) + [70],
        "width": 1000,
        "quality": 80,
    },
]


def render_pdf(pdf_path, out_dir, width, quality, trim=False, keep=None):
    """PDF 逐页渲染为 JPG。

    trim=True 按 TrimBox 裁掉裁切线与出血区；
    keep 给出要导出的 1 起页码列表，None 表示全部。
    """
    doc = pymupdf.open(pdf_path)
    numbers = list(range(1, doc.page_count + 1)) if keep is None else list(keep)
    written = []
    for i, no in enumerate(numbers):
        page = doc[no - 1]
        clip = page.trimbox if trim else None
        box = clip if clip is not None else page.rect
        zoom = width / box.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, alpha=False)
        path = os.path.join(out_dir, "%02d.jpg" % (i + 1))
        pix.save(path, jpg_quality=quality)
        written.append(path)
    doc.close()
    return len(written), sum(os.path.getsize(p) for p in written)


def render_images(src_dir, out_dir, width, quality):
    """图片文件夹（如扫描件 2.jpg~11.jpg）按数字顺序导出为 01.jpg..."""
    files = sorted(
        glob.glob(os.path.join(src_dir, "*.jpg")) + glob.glob(os.path.join(src_dir, "*.png")),
        key=lambda p: [int(t) for t in re.findall(r"\d+", os.path.basename(p))] or [0],
    )
    written = []
    for i, src in enumerate(files):
        im = Image.open(src).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        path = os.path.join(out_dir, "%02d.jpg" % (i + 1))
        im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
        written.append(path)
    return len(written), sum(os.path.getsize(p) for p in written)


def render(book):
    out_dir = os.path.join(OUT_ROOT, book["key"])
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    kind, src = book["source"]
    width = book.get("width", TARGET_W)
    quality = book.get("quality", QUALITY)
    if kind == "pdf":
        count, total = render_pdf(src, out_dir, width, quality,
                                  book.get("trim", False), book.get("keep"))
    else:
        count, total = render_images(src, out_dir, width, quality)

    print("%-9s %-26s 页数=%2d  合计=%5.1f MB"
          % (book["key"], book["label"], count, total / 1048576))
    return count


if __name__ == "__main__":
    # 可只传 key 重跑某本，如: python render_books.py datangxi
    wanted = sys.argv[1:]
    for b in BOOKS:
        if not wanted or b["key"] in wanted:
            render(b)
