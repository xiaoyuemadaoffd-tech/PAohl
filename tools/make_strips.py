# -*- coding: utf-8 -*-
"""把同尺寸的连续页面竖向合并成「长条拼图」，把上传 GitHub 的文件数降到 1/4。

为什么需要它
------------
GitHub 网页版拖拽上传一次最多 100 个文件，而逐页导出的图片有 130+ 个。
合并后同一组页面只占 1~2 个文件，网页端用 CSS 把长图裁出其中一页
（见 index.html 里的 .strip 规则），显示效果与逐页图片一致。

用法
----
    python make_strips.py

输入：逐页原图（优先取 <作品集>/images/…，逐页图归档后自动改读
      <作品集同级>/_作品集原图存档/images/…）
输出：<作品集>/images/sheets/<name>-<k>.jpg

改动页数 / 换图后重新运行即可，末尾会打印需要同步到 index.html 的配置行。
"""
import os

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO = os.path.dirname(BASE)                      # 2026年投递
ARCHIVE = os.path.join(os.path.dirname(PORTFOLIO), "_作品集原图存档")
OUT_DIR = os.path.join(PORTFOLIO, "images", "sheets")

# 长图高度上限：一张图太高的画，部分浏览器/显卡会拒绝渲染或解码很慢。
# 超过就自动拆成多张（文件名 -1 / -2 …），网页端按「第几页」自动选图。
MAX_SHEET_H = 16000


# 逐页原图的根目录：原图还在 images/ 就用它，已归档就改读存档目录
def src_root():
    for root in (os.path.join(PORTFOLIO, "images"), os.path.join(ARCHIVE, "images")):
        if os.path.isdir(os.path.join(root, "books")):
            return root
    raise SystemExit("找不到逐页原图目录（images/ 或 _作品集原图存档/images/）")


def seq(root, sub, count, pad=2):
    """按 01.jpg / 1.jpg 的命名规律列出逐页原图。"""
    d = os.path.join(root, sub)
    return [os.path.join(d, "%s.jpg" % str(i + 1).zfill(pad)) for i in range(count)]


def fansheyingzhe(root):
    """《反摄影者》：封面 → 内页 → 封底，跳过纯色空页（3/5/13/14…）。

    封底（扫描件 1）排在最后，配合 index.html 里 p6 的 showCover：
    第 1 屏是封面单独一屏，最后一屏收封底，翻起来跟真书一样。
    以前封底是跟封面并排放在第 1 屏的，那时需要对缝微调海平面，现在不需要了。
    """
    d = os.path.join(root, "photos")
    keep = [2, 4, 6, 7, 8, 9, 10, 11, 12, 15, 16, 1]   # 2=封面，1=封底
    return [os.path.join(d, "books2 (%d).jpg" % n) for n in keep]


def funerary(root):
    """隋唐随葬品可视化：第 1 张是截图（png），其余是照片（jpg）。"""
    d = os.path.join(root, "funerary")
    return ([os.path.join(d, "1.png")] +
            [os.path.join(d, "%d.jpg" % i) for i in range(2, 6)])


# 每一组要合并的页面。
#   src/sub + count  → 按命名规律取图（pad=1 时不补零）
#   files            → 直接给出文件清单（命名不规律时用）
#   cell             → 页面尺寸不一致时，统一等比装进这个白底格子
#   seam             → {页序号: dict(scale_y, shift_y)}，跨页对缝微调。
#                      当前没有用到，留着备用（比如以后又想把「封底+封面」并排成一屏，
#                      两页的海平面需要对齐时就派得上用场）
#   cover            → 页序号：把该页另外导一张 <name>-cover.jpg 单独的小图，
#                      因为作品卡片是「横向宽扁」的框子（object-cover 刀一刀），
#                      用长图裁切撑不满框子，只能单独给一张
SETS = [
    # 四本展册内页：同一本书逐页尺寸完全一致，直接竖排。
    # cover=0：另导一张封面小图给合集弹窗的展册卡片用（卡片只有 150~200px 宽，
    # 不另导的话打开弹窗就要先把 4 张 2MB 的长图全下拉一遍）
    dict(name="picasso", sub="books/picasso", count=12, q=87, cover=0, cover_w=600),
    dict(name="qitan", sub="books/qitan", count=12, q=87, cover=0, cover_w=600),
    dict(name="gejian", sub="books/gejian", count=14, q=87, cover=0, cover_w=600),
    dict(name="bologna", sub="books/bologna", count=10, q=87, cover=0, cover_w=600),
    dict(name="datangxi", sub="books/datangxi", count=20, q=87),
    # ART021 现场：只有第 1 张是 1600×900，其余是 2667×1500，统一进 16:9 格子。
    # 格子取 2400×1350（大图查看时最大也就显示到 ~1240px 宽，够 2 倍屏），
    # 比原图小一圈可以明显减小长图体积
    dict(name="art021", sub="art021", count=6, pad=1, cell=(2400, 1350), q=88),
    # 成人美育课件：8 张里 1 张是 1334×750，统一进 16:9 格子
    dict(name="gezhi", sub="gezhi", count=8, pad=1, cell=(2400, 1350), q=88),
    # 可视化项目截图：比例 1.74~1.83 略有差异，统一进 16:9 格子
    dict(name="funerary", files=funerary, cell=(2400, 1350), q=90, cover=0),
    # 《反摄影者》实拍扫描件：封面在前、封底在后（翻书顺序），
    # 卡片封面取第 1 格，就是封面本身
    dict(name="fansheyingzhe", files=fansheyingzhe, q=88, cover=0),
]


def open_rgb(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        # 有透明像素的话平铺到白底上会变样，先提示一声
        im = im.convert("RGBA")
        if im.getchannel("A").getextrema()[0] < 255:
            print("    注意：%s 含透明像素，已按白底压平" % os.path.basename(path))
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im.convert("RGB")


def paste_clipped(cell, img, x, y):
    """把 img 贴到 cell 的 (x, y)，超出单元格的部分裁掉（允许负坐标）。"""
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(img.width, cell.width - x), min(img.height, cell.height - y)
    if sx1 > sx0 and sy1 > sy0:
        cell.paste(img.crop((sx0, sy0, sx1, sy1)), (x + sx0, y + sy0))


def make_cell(page, cw, ch):
    """尺寸不一致的页面：等比缩放后居中放进白底格子（不裁内容）。"""
    cell = Image.new("RGB", (cw, ch), "white")
    if page.size == (cw, ch):
        cell.paste(page, (0, 0))
        return cell
    r = min(cw / page.width, ch / page.height)
    w, h = max(1, round(page.width * r)), max(1, round(page.height * r))
    paste_clipped(cell, page.resize((w, h), Image.LANCZOS), (cw - w) // 2, (ch - h) // 2)
    return cell


def build(cfg, root):
    files = (cfg["files"](root) if callable(cfg.get("files"))
             else seq(root, cfg["sub"], cfg["count"], cfg.get("pad", 2)))
    missing = [f for f in files if not os.path.isfile(f)]
    if missing:
        raise SystemExit("缺文件：\n  " + "\n  ".join(missing))

    pages = [open_rgb(f) for f in files]
    src_px = sum(p.width * p.height for p in pages)
    src_kb = sum(os.path.getsize(f) for f in files) // 1024

    cw, ch = cfg.get("cell", pages[0].size)
    if "cell" not in cfg and any(p.size != (cw, ch) for p in pages):
        raise SystemExit("%s：逐页尺寸不一致，需要显式指定 cell=" % cfg["name"])

    cells = []
    for i, page in enumerate(pages):
        if (cw, ch) == page.size:
            cell = page
        else:
            cell = make_cell(page, cw, ch)
        seam = (cfg.get("seam") or {}).get(i)
        if seam:
            # 复刻原来 CSS 的 transform: translateY(负值) scaleY(>1)：
            # 先纵向放大（视觉上围绕原图中心，所以放大后要减掉多出来高度的一半），
            # 再整体上移，超出格子的部分被裁掉
            h2 = round(ch * seam["scale_y"])
            box = Image.new("RGB", (cw, ch), "white")
            paste_clipped(box, cell.resize((cw, h2), Image.LANCZOS),
                          0, round((ch - h2) / 2 + seam["shift_y"] * ch))
            cell = box
        cells.append(cell)

    per = max(1, MAX_SHEET_H // ch)
    os.makedirs(OUT_DIR, exist_ok=True)

    out_kb = 0
    sheets = 0
    for k in range(0, len(cells), per):
        chunk = cells[k:k + per]
        sheet = Image.new("RGB", (cw, ch * len(chunk)), "white")
        for j, cell in enumerate(chunk):
            sheet.paste(cell, (0, j * ch))
        path = os.path.join(OUT_DIR, "%s-%d.jpg" % (cfg["name"], k // per + 1))
        sheet.save(path, "JPEG", quality=cfg["q"], optimize=True, progressive=True)
        out_kb += os.path.getsize(path) // 1024
        sheets += 1
        print("    %-28s %5d×%-6d %5dKB" % (os.path.basename(path), sheet.width,
                                            sheet.height, os.path.getsize(path) // 1024))

    # 卡片封面：作品卡片是横向宽扁的框子，长图裁切撑不满，另外导一张普通小图
    if cfg.get("cover") is not None:
        cover = cells[cfg["cover"]]
        max_w = cfg.get("cover_w", 1200)
        if cover.width > max_w:
            h = round(cover.height * max_w / cover.width)
            cover = cover.resize((max_w, h), Image.LANCZOS)
        path = os.path.join(OUT_DIR, "%s-cover.jpg" % cfg["name"])
        cover.save(path, "JPEG", quality=cfg["q"], optimize=True, progressive=True)
        out_kb += os.path.getsize(path) // 1024
        print("    %-28s %5d×%-6d %5dKB（卡片封面）"
              % (os.path.basename(path), cover.width, cover.height,
                 os.path.getsize(path) // 1024))

    print("  %s：%d 页 → %d 张长图；%dKB → %dKB"
          % (cfg["name"], len(cells), sheets, src_kb, out_kb))
    print("  JS: stripSet('%s', %d / %d, %d, %d)," % (cfg["name"], cw, ch, len(cells), per))
    print()
    return len(cells), sheets, src_kb, out_kb


def main():
    root = src_root()
    print("逐页原图：%s" % root)
    print("输出目录：%s\n" % OUT_DIR)
    total_pages = total_sheets = total_in = total_out = 0
    for cfg in SETS:
        pages, sheets, src_kb, out_kb = build(cfg, root)
        total_pages += pages
        total_sheets += sheets
        total_in += src_kb
        total_out += out_kb
    print("合计：%d 页逐页图（%dKB）→ %d 张长图（%dKB）"
          % (total_pages, total_in, total_sheets, total_out))


if __name__ == "__main__":
    main()
