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

def parse_defines(text):
    return {m[1]: int(m[2]) for m in re.finditer(r"#define\s+(\w+)\s+(\d+)", text)}

def parse_display_names(text):
    return re.findall(r'display-name\s*=\s*"([^"]+)"', text)

def parse_overlay(text):
    m = re.search(r"zip_temp_layer\s+(\d+)", text)
    aml = int(m.group(1)) if m else None
    m2 = re.search(r"scroller\s*\{[^}]*layers\s*=\s*<([^>]+)>", text, re.DOTALL)
    scroll = set(map(int, m2.group(1).split())) if m2 else set()
    return aml, scroll

# ── Static layer descriptions (keyed by display-name) ──────────────────────────

LAYER_COLOR = {
    "MAC":   "#2980B9",
    "WIN":   "#2980B9",
    "SYM":   "#16A085",
    "NUM":   "#16A085",
    "NAV-W": "#D35400",
    "NAV-M": "#D35400",
    "MOUSE": "#7D3C98",
    "BLE":   "#C0392B",
}

ACTIVATION = {
    "MAC":   "default  /  BT0",
    "WIN":   "BT1  /  BT2",
    "SYM":   "Space 長押し",
    "NUM":   "LANG2 長押し  (英数キー)",
    "NAV-W": "LANG1 長押し  (WIN ベース時)",
    "NAV-M": "LANG1 長押し  (MAC ベース時)",
    "MOUSE": "ボール操作で自動遷移  /  500ms で復帰",
    "BLE":   "英数 + かな  同時長押し",
}

# (background, text, label)
BALL_CURSOR  = ("#AED6F1", "#1A5276", "カーソル")
BALL_AUTO    = ("#D5F5E3", "#1E8449", "→ 自動で MOUSE へ")
BALL_SCROLL  = ("#A9DFBF", "#1E8449", "スクロール")
BALL_BUTTONS = ("#D7BDE2", "#6C3483", "MB1 · MB2 · MB3 · MB4 · MB5")
BALL_VOLUME  = ("#FAD7A0", "#935116", "ボリューム  (エンコーダ共通)")

# ── SVG primitives ──────────────────────────────────────────────────────────────

W      = 740
ROW_H  = 48
TITLE_H = 54
HEAD_H = 36
PAD    = 16

# column x positions and widths
CX = [0, 50, 160, 430]
CW = [50, 110, 270, W - 430]

def _attrs(**kw):
    return " ".join(f'{k.replace("_","-")}="{v}"' for k, v in kw.items() if v is not None)

def rect(x, y, w, h, fill, rx=None, stroke=None, stroke_width=None):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"' \
           + (f' rx="{rx}"' if rx else "") \
           + (f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else "") \
           + "/>"

def text(x, y, txt, anchor="start", size=13, bold=False, fill="#2C3E50"):
    fw = "bold" if bold else "normal"
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}"'
            f' font-family="sans-serif" font-weight="{fw}" fill="{fill}">{txt}</text>')

def line(x1, y1, x2, y2, color="#DEDEDE", width=1):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'

def pill(cx, cy, label, bg, fg, min_w=90):
    pw = max(len(label) * 7 + 24, min_w)
    ph = 26
    px, py = cx - pw // 2, cy - ph // 2
    return (rect(px, py, pw, ph, bg, rx=13)
            + text(cx, cy + 5, label, anchor="middle", size=11, bold=True, fill=fg))

# ── Main SVG builder ────────────────────────────────────────────────────────────

def build(display_names, aml, scroll_layers):
    n = len(display_names)
    H = TITLE_H + HEAD_H + n * ROW_H + PAD + 18

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    # ── background ──
    out.append(rect(0, 0, W, H, "#F8F9FA", rx=10))

    # ── title bar ──
    out.append(rect(0, 0, W, TITLE_H, "#1B2631", rx=10))
    out.append(rect(0, TITLE_H - 10, W, 10, "#1B2631"))  # flatten bottom
    out.append(text(W // 2, 35, "moNa2 — Layer &amp; Trackball Behavior",
                    anchor="middle", size=18, bold=True, fill="#FFFFFF"))

    # ── header row ──
    hy = TITLE_H
    out.append(rect(0, hy, W, HEAD_H, "#2C3E50"))
    for col_x, col_w, label in [
        (CX[0], CW[0], "#"),
        (CX[1], CW[1], "Layer"),
        (CX[2], CW[2], "Activation"),
        (CX[3], CW[3], "Trackball"),
    ]:
        anchor = "middle" if label in ("#", "Layer", "Trackball") else "start"
        tx = col_x + (col_w // 2 if anchor == "middle" else 10)
        out.append(text(tx, hy + 24, label, anchor=anchor, size=12, bold=True, fill="#BDC3C7"))
    out.append(line(0, hy + HEAD_H, W, hy + HEAD_H, color="#3D566E"))

    # ── data rows ──
    for i, name in enumerate(display_names):
        ry = TITLE_H + HEAD_H + i * ROW_H
        cy = ry + ROW_H // 2
        bg = "#FFFFFF" if i % 2 == 0 else "#F2F3F4"
        out.append(rect(0, ry, W, ROW_H, bg))
        out.append(line(0, ry + ROW_H, W, ry + ROW_H))

        color = LAYER_COLOR.get(name, "#95A5A6")

        # col 0: layer index badge
        bx = CX[0] + CW[0] // 2
        out.append(rect(bx - 16, cy - 15, 32, 30, color, rx=5))
        out.append(text(bx, cy + 6, str(i), anchor="middle", size=13, bold=True, fill="#FFFFFF"))

        # col 1: layer name
        star = " ★" if i == 0 else ""
        out.append(text(CX[1] + 8, cy + 6, name + star, size=13, bold=True, fill=color))

        # col 2: activation
        act = ACTIVATION.get(name, "—")
        out.append(text(CX[2] + 10, cy + 6, act, size=11, fill="#34495E"))

        # col 3: trackball
        ball_cx = CX[3] + CW[3] // 2
        if i in scroll_layers:
            out.append(pill(ball_cx, cy, BALL_SCROLL[2], BALL_SCROLL[0], BALL_SCROLL[1]))
        elif i == aml:
            out.append(pill(ball_cx, cy, BALL_BUTTONS[2], BALL_BUTTONS[0], BALL_BUTTONS[1], min_w=CW[3] - 16))
        elif name == "BLE":
            out.append(pill(ball_cx, cy, BALL_VOLUME[2], BALL_VOLUME[0], BALL_VOLUME[1]))
        else:
            # cursor pill + auto-arrow
            cw = 76; ch = 26
            px = CX[3] + 8; py = cy - ch // 2
            out.append(rect(px, py, cw, ch, BALL_CURSOR[0], rx=13))
            out.append(text(px + cw // 2, cy + 5, BALL_CURSOR[2],
                            anchor="middle", size=11, bold=True, fill=BALL_CURSOR[1]))
            out.append(text(px + cw + 8, cy + 5, BALL_AUTO[2], size=10, fill=BALL_AUTO[1]))

        # column dividers
        for cx_div in CX[1:]:
            out.append(line(cx_div, ry, cx_div, ry + ROW_H))

    # ── outer border ──
    out.append(rect(0, 0, W, H, "none", rx=10,
                    stroke="#BDC3C7", stroke_width="1.5"))

    # ── footer note ──
    fy = TITLE_H + HEAD_H + n * ROW_H + PAD + 4
    out.append(text(PAD, fy,
                    "★ = デフォルト層（電源投入時）　　スクロール = LANG1 / LANG2 長押し中に有効",
                    size=10, fill="#95A5A6"))

    out.append('</svg>')
    return "\n".join(out)


def main():
    ktext = KEYMAP.read_text(encoding="utf-8")
    otext = OVERLAY.read_text(encoding="utf-8")
    names   = parse_display_names(ktext)
    defines = parse_defines(ktext)
    aml, scroll = parse_overlay(otext)
    svg = build(names, aml, scroll)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Written: {OUTPUT}  (aml={aml}, scroll={sorted(scroll)})")

if __name__ == "__main__":
    main()
