#!/usr/bin/env python3
"""从 squirrel.yaml 的 preset_color_schemes 生成皮肤总览预览图(每套皮肤双背景)。
输出两张 SVG:
  light.svg — 白底页面,包含全部皮肤的候选窗(模拟浅色模式壁纸)
  dark.svg  — 黑底页面,包含全部皮肤的候选窗(模拟深色模式壁纸)
用法: python3 gen_svg.py <squirrel.yaml> <输出目录>
"""
import re, sys, os

src_path, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

def rime_color(v):
    m = re.fullmatch(r"0x([0-9a-fA-F]{6,8})", v.strip())
    if not m:
        return None
    h = m.group(1)
    if len(h) == 8:
        h = h[2:]
    b, g, r = h[0:2], h[2:4], h[4:6]   # Rime 0xBBGGRR → RGB
    return f"#{r}{g}{b}".lower()

schemes, cur, order = {}, None, []
started = False
for line in open(src_path, encoding="utf-8"):
    if line.startswith("preset_color_schemes:"):
        started = True
        continue
    if not started:
        continue
    m1 = re.match(r"^  ([a-z_]+):\s*$", line)
    if m1:
        cur = m1.group(1)
        if cur not in schemes:
            schemes[cur] = {}
            order.append(cur)
        continue
    m2 = re.match(r"^    ([a-z_]+):\s*(.+?)\s*(?:#.*)?$", line)
    if m2 and cur:
        schemes[cur][m2.group(1)] = m2.group(2).strip().strip('"')

def C(s, *keys, default="#333333"):
    for k in keys:
        if k in s:
            v = rime_color(s[k])
            if v:
                return v
    return default

FONT = "-apple-system,'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif"

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text_w(t, size):
    return sum(size if ord(ch) > 0x2E7F else size * 0.58 for ch in t)

def window_mock(x0, y0, s):
    back   = C(s, "back_color")
    border = C(s, "border_color", default=back)
    text   = C(s, "text_color", "candidate_text_color")
    cand   = C(s, "candidate_text_color", default=text)
    label  = C(s, "label_color", "candidate_text_color", default=cand)
    hl_t   = C(s, "hilited_candidate_text_color", "hilited_text_color", "text_color")
    hl_b   = C(s, "hilited_candidate_back_color", "hilited_back_color", default="#3478f6")
    hl_l   = C(s, "hilited_label_color", "hilited_candidate_text_color", default=hl_t)
    cmt    = C(s, "comment_text_color", default="#999999")
    hl_c   = C(s, "hilited_comment_text_color", "comment_text_color", default=cmt)

    w, h = 380, 84
    p = [f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="7" '
         f'fill="{back}" stroke="{border}" stroke-width="1"/>',
         f'<text x="{x0+18}" y="{y0+26}" font-family="{FONT}" font-size="13" fill="{text}">shaijing</text>']
    ty = y0 + 60
    x = x0 + 16
    for lab, word, comment, hi in [("1.", "曬經", "", False), ("2.", "石景", "shaijing", True),
                                   ("3.", "晒镜", "", False), ("4.", "山寨", "", False)]:
        if hi:
            bw = text_w(lab + word, 15) + text_w("  " + comment, 11) + 16
            p.append(f'<rect x="{x}" y="{ty-21}" width="{bw:.0f}" height="30" rx="4" fill="{hl_b}"/>')
            p.append(f'<text x="{x+8}" y="{ty}" font-family="{FONT}" font-size="15">'
                     f'<tspan fill="{hl_l}">{esc(lab)}</tspan>'
                     f'<tspan fill="{hl_t}" dx="2">{esc(word)}</tspan>'
                     f'<tspan fill="{hl_c}" font-size="11" dx="8">{esc(comment)}</tspan></text>')
            x += bw + 10
        else:
            p.append(f'<text x="{x}" y="{ty}" font-family="{FONT}" font-size="15">'
                     f'<tspan fill="{label}">{esc(lab)}</tspan>'
                     f'<tspan fill="{cand}" dx="2">{esc(word)}</tspan></text>')
            x += text_w(lab + word, 15) + 24
    return "\n".join(p)

# ---- 页面参数:2 列网格 ----
KEYS = [k for k in order if k != "native"]          # native 无固定色值
COLS, CELL_W, CELL_H, MARGIN, HEADER = 2, 470, 168, 40, 86
skipped = [k for k in order if k == "native"]
def page_svg(bg, title_color, sub_color, note_color, title, outfile):
    rows = (len(KEYS) + COLS - 1) // COLS
    W = COLS * CELL_W + (COLS + 1) * MARGIN
    H = HEADER + rows * CELL_H + MARGIN
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="{bg}"/>',
         f'<text x="{MARGIN}" y="46" font-family="{FONT}" font-size="26" fill="{title_color}">{esc(title)}</text>',
         f'<text x="{MARGIN}" y="72" font-family="{FONT}" font-size="13" fill="{note_color}">'
         f'Squirrel 1.1.2 官方内置皮肤 · 候选窗示意(横排/圆角7px) · 色值取自 SharedSupport/squirrel.yaml'
         f'{(" · 跳过 native(系统配色)" if skipped else "")}</text>']
    for i, key in enumerate(KEYS):
        s = schemes[key]
        col, row = i % COLS, i // COLS
        cx = MARGIN + col * (CELL_W + MARGIN)
        cy = HEADER + row * CELL_H
        name = esc(s.get("name", key))
        p.append(f'<text x="{cx}" y="{cy+18}" font-family="{FONT}" font-size="15" fill="{title_color}">'
                 f'{name} <tspan font-size="11" fill="{sub_color}">{key}</tspan></text>')
        p.append(window_mock(cx, cy + 30, s))
    p.append("</svg>")
    path = os.path.join(out_dir, outfile)
    open(path, "w", encoding="utf-8").write("\n".join(p))
    print(f"{outfile}: {len(KEYS)} 套皮肤, {W}x{H}")

page_svg("#ffffff", "#1d1d1f", "#86868b", "#86868b", "鼠须管皮肤总览 · 浅色模式(白底)", "light.svg")
page_svg("#000000", "#f5f5f7", "#6e6e73", "#6e6e73", "鼠须管皮肤总览 · 深色模式(黑底)", "dark.svg")
