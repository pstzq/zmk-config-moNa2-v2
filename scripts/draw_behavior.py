#!/usr/bin/env python3
"""
moNa2 Layer & Trackball Behavior SVG Generator.

Reads mona2.keymap and mona2_r.overlay; outputs keymap-drawer/mona2_behavior.svg.
Invoked by .github/workflows/draw.yml on every keymap push.
"""
import re
from pathlib import Path

ROOT    = Path(__file__).parent.parent
KEYMAP  = ROOT / "config" / "mona2.keymap"
OVERLAY = ROOT / "boards" / "shields" / "mona2" / "mona2_r.overlay"
OUTPUT  = ROOT / "keymap-drawer" / "mona2_behavior.svg"

# ── Parse source files ──────────────────────────────────────────────────────────

def parse_display_names(text):
    return re.findall(r'display-name\s*=\s*"([^"]+)"', text)

def _subnode_layers(text, node):
    m = re.search(node + r"\s*\{[^}]*layers\s*=\s*<([^>]+)>", text, re.DOTALL)
    return set(map(int, m.group(1).split())) if m else set()

def parse_overlay(text):
    m = re.search(r"zip_temp_layer\s+(\d+)", text)
    aml     = int(m.group(1)) if m else None
    scroll  = _subnode_layers(text, "scroller")
    pan     = _subnode_layers(text, "panner")
    gesture = _subnode_layers(text, "gesturer_mac") | _subnode_layers(text, "gesturer_win")
    keybind = _subnode_layers(text, "cursor_keys")
    return aml, scroll, pan, gesture, keybind

# ── Static layer descriptions (keyed by display-name) ──────────────────────────

# Colors harmonized with keymap-drawer GitHub palette
LAYER_COLOR = {
    "MAC":    "#0366d6",
    "WIN":    "#0366d6",
    "O24":    "#6f42c1",
    "SYM":    "#28a745",
    "NUM":    "#28a745",
    "NAV-W":  "#e36209",
    "NAV-M":  "#e36209",
    "MOUSE":  "#6f42c1",
    "BLE":    "#cb2431",
    "PAN":    "#0598a7",
    "SNAP-M": "#d03592",
    "SNAP-W": "#d03592",
    "CURSOR": "#0075ca",
}

ACTIVATION = {
    "MAC":    "default  /  BT0",
    "WIN":    "BT1  /  BT2",
    "O24":    "Q + P 同時押し（トグル）",
    "SYM":    "Space 長押し",
    "NUM":    "Enter 長押し",
    "NAV-W":  "英数 or かな 長押し  (WIN ベース時)",
    "NAV-M":  "英数 or かな 長押し  (MAC ベース時)",
    "MOUSE":  "ボール操作で自動遷移  /  500ms で復帰",
    "BLE":    "英数 ＆ かな  同時押し (コンボ)",
    "PAN":    "P 長押し",
    "SNAP-M": "Q 長押し  (MAC ベース時)",
    "SNAP-W": "Q 長押し  (WIN ベース時)",
    "CURSOR": "— （未実装・予約済み）",
}

# (background, foreground, label)  — pastel fills consistent with keymap-drawer combo/held colors
BALL_CURSOR  = ("#ddf4ff", "#0366d6", "カーソル")
BALL_AUTO    = ("#dcffe4", "#28a745", "→ 自動で MOUSE へ")
BALL_SCROLL  = ("#dcffe4", "#28a745", "スクロール")
BALL_BUTTONS = ("#f5d0f5", "#6f42c1", "MB1 · MB2 · MB3 · MB4 · MB5")
BALL_VOLUME  = ("#fff3cd", "#856404", "ボリューム（エンコーダ共通）")
BALL_PAN     = ("#d1ecf1", "#0598a7", "2D パン（自由スクロール）")
BALL_GESTURE = ("#ffe8cc", "#e36209", "ジェスチャー（ウィンドウスナップ）")
BALL_KEYBIND = ("#ddf4ff", "#0075ca", "矢印キー入力")

# ── Design tokens (aligned with keymap-drawer) ──────────────────────────────────

FONT     = "SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace"
C_BG     = "#ffffff"
C_BG_ALT = "#f6f8fa"
C_BORDER = "#c9cccf"
C_TEXT   = "#24292e"
C_MUTED  = "#6a737d"

W       = 788
ROW_H   = 44
TITLE_H = 36
HEAD_H  = 30
PAD     = 12

# column x positions and widths (must sum to W)
CX = [0,   52,  170, 450]
CW = [52,  118, 280, 338]

# ── SVG primitives ──────────────────────────────────────────────────────────────

def rect(x, y, w, h, fill, rx=None, stroke=None, stroke_width=None):
    s  = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
    s += f' rx="{rx}"' if rx else ""
    s += f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return s + "/>"

def text(x, y, txt, anchor="start", size=13, bold=False, fill=C_TEXT):
    fw = "bold" if bold else "normal"
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}"'
            f' font-family="{FONT}" font-weight="{fw}" fill="{fill}">{txt}</text>')

def line(x1, y1, x2, y2, color=C_BORDER, width=1):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'

def pill(cx, cy, label, bg, fg, min_w=90):
    pw = max(len(label) * 7 + 20, min_w)
    ph = 22
    px, py = cx - pw // 2, cy - ph // 2
    return (rect(px, py, pw, ph, bg, rx=11, stroke=fg, stroke_width="0.8")
            + text(cx, cy + 4, label, anchor="middle", size=11, bold=True, fill=fg))

# ── Main SVG builder ────────────────────────────────────────────────────────────

def build(display_names, aml, scroll_layers, pan_layers, gesture_layers, keybind_layers):
    n = len(display_names)
    H = TITLE_H + HEAD_H + n * ROW_H + PAD + 14

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    # background
    out.append(rect(0, 0, W, H, C_BG, rx=6))

    # title
    out.append(text(PAD, TITLE_H // 2 + 6,
                    "moNa2 — Layer &amp; Trackball Behavior",
                    anchor="start", size=14, bold=True, fill=C_TEXT))
    out.append(line(0, TITLE_H, W, TITLE_H))

    # header row
    hy = TITLE_H
    out.append(rect(0, hy, W, HEAD_H, C_BG_ALT))
    for col_x, col_w, label in [
        (CX[0], CW[0], "#"),
        (CX[1], CW[1], "Layer"),
        (CX[2], CW[2], "Activation"),
        (CX[3], CW[3], "Trackball"),
    ]:
        center = label in ("#", "Trackball")
        tx     = col_x + (col_w // 2 if center else 8)
        out.append(text(tx, hy + HEAD_H // 2 + 5, label,
                        anchor="middle" if center else "start",
                        size=11, bold=True, fill=C_MUTED))
    out.append(line(0, hy + HEAD_H, W, hy + HEAD_H))

    # data rows
    for i, name in enumerate(display_names):
        ry = TITLE_H + HEAD_H + i * ROW_H
        cy = ry + ROW_H // 2
        bg = C_BG if i % 2 == 0 else C_BG_ALT
        out.append(rect(0, ry, W, ROW_H, bg))
        out.append(line(0, ry + ROW_H, W, ry + ROW_H))

        color = LAYER_COLOR.get(name, C_MUTED)

        # col 0: index badge
        bx = CX[0] + CW[0] // 2
        out.append(rect(bx - 14, cy - 13, 28, 26, color, rx=4))
        out.append(text(bx, cy + 5, str(i), anchor="middle", size=12, bold=True, fill="#ffffff"))

        # col 1: layer name
        star = " ★" if i == 0 else ""
        out.append(text(CX[1] + 8, cy + 5, name + star, size=12, bold=True, fill=color))

        # col 2: activation
        act = ACTIVATION.get(name, "—")
        out.append(text(CX[2] + 10, cy + 5, act, size=11, fill=C_TEXT))

        # col 3: trackball behavior
        ball_cx = CX[3] + CW[3] // 2
        if i in scroll_layers:
            out.append(pill(ball_cx, cy, BALL_SCROLL[2], BALL_SCROLL[0], BALL_SCROLL[1]))
        elif i in pan_layers:
            out.append(pill(ball_cx, cy, BALL_PAN[2], BALL_PAN[0], BALL_PAN[1], min_w=CW[3] - 20))
        elif i in gesture_layers:
            out.append(pill(ball_cx, cy, BALL_GESTURE[2], BALL_GESTURE[0], BALL_GESTURE[1], min_w=CW[3] - 20))
        elif i in keybind_layers:
            out.append(pill(ball_cx, cy, BALL_KEYBIND[2], BALL_KEYBIND[0], BALL_KEYBIND[1]))
        elif name == "CURSOR":
            cw = 72; ch = 22
            px = CX[3] + 10; py = cy - ch // 2
            out.append(rect(px, py, cw, ch, "#f0f0f0", rx=11, stroke="#aaaaaa", stroke_width="0.8"))
            out.append(text(px + cw // 2, cy + 4, "（なし）", anchor="middle", size=11, bold=True, fill="#888888"))
        elif i == aml:
            out.append(pill(ball_cx, cy, BALL_BUTTONS[2], BALL_BUTTONS[0], BALL_BUTTONS[1], min_w=CW[3] - 20))
        elif name == "BLE":
            out.append(pill(ball_cx, cy, BALL_VOLUME[2], BALL_VOLUME[0], BALL_VOLUME[1]))
        else:
            cw = 72; ch = 22
            px = CX[3] + 10; py = cy - ch // 2
            out.append(rect(px, py, cw, ch, BALL_CURSOR[0], rx=11,
                            stroke=BALL_CURSOR[1], stroke_width="0.8"))
            out.append(text(px + cw // 2, cy + 4, BALL_CURSOR[2],
                            anchor="middle", size=11, bold=True, fill=BALL_CURSOR[1]))
            out.append(text(px + cw + 8, cy + 4, BALL_AUTO[2], size=10, fill=BALL_AUTO[1]))

        # column dividers
        for cx_div in CX[1:]:
            out.append(line(cx_div, ry, cx_div, ry + ROW_H))

    # outer border (drawn last to sit on top of row backgrounds)
    out.append(rect(0, 0, W, H, "none", rx=6, stroke=C_BORDER, stroke_width="1"))

    # footer
    fy = TITLE_H + HEAD_H + n * ROW_H + PAD
    out.append(text(PAD, fy,
                    "★ = デフォルト層（電源投入時）　　スクロール = NUM / NAV 層で有効",
                    size=10, fill=C_MUTED))

    out.append('</svg>')
    return "\n".join(out)


def main():
    ktext = KEYMAP.read_text(encoding="utf-8")
    otext = OVERLAY.read_text(encoding="utf-8")
    names                          = parse_display_names(ktext)
    aml, scroll, pan, gesture, keybind = parse_overlay(otext)
    svg = build(names, aml, scroll, pan, gesture, keybind)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Written: {OUTPUT}  (aml={aml}, scroll={sorted(scroll)}, "
          f"pan={sorted(pan)}, gesture={sorted(gesture)}, keybind={sorted(keybind)})")

if __name__ == "__main__":
    main()
