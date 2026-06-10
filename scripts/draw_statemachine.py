#!/usr/bin/env python3
"""
moNa2 Layer State Machine SVG Generator.

Reads static layer/transition definitions and outputs
keymap-drawer/mona2_statemachine.svg.
"""
import math
from pathlib import Path

ROOT   = Path(__file__).parent.parent
OUTPUT = ROOT / "keymap-drawer" / "mona2_statemachine.svg"

FONT   = "SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace"
C_BG   = "#ffffff"
C_BOR  = "#c9cccf"
C_TEXT = "#24292e"
C_MUT  = "#6a737d"

LAYER_COLOR = {
    "MAC":    "#0366d6", "WIN":    "#0366d6",
    "O24":    "#6f42c1",
    "SYM":    "#28a745", "NUM":    "#28a745",
    "NAV-M":  "#e36209", "NAV-W":  "#e36209",
    "MOUSE":  "#6f42c1",
    "BLE":    "#cb2431",
    "PAN":    "#0598a7",
    "SNAP-M": "#d03592", "SNAP-W": "#d03592",
    "CURSOR": "#cccccc",  # grayed: reserved but unimplemented
}

W, H   = 860, 580
NW, NH = 96, 32   # node box width / height
MAC_C  = "#0366d6"
WIN_C  = "#e36209"
BT_C   = "#6a737d"
O24_C  = "#6f42c1"

# Node center positions
NODES = {
    "SYM":    (140,  70),
    "NUM":    (268,  70),
    "MOUSE":  (430,  70),
    "BLE":    (592,  70),
    "PAN":    (720,  70),
    "NAV-M":  (50,  238),
    "MAC":    (210, 238),
    "WIN":    (650, 238),
    "NAV-W":  (810, 238),
    "SNAP-M": (210, 402),
    "SNAP-W": (650, 402),
    "CURSOR": (430, 470),  # reserved / unimplemented
    "O24":    (588, 470),  # Q+P toggle
}

# (src, dst, label, curve_offset, color_key)
# curve_offset: perpendicular bend in px (+/- to separate parallel edges)
# color_key: "mac", "win", "bt", "o24", "hidden"
EDGES = [
    # BT profile: handled specially as bidirectional
    ("MAC", "WIN",    "BT profile",  0,    "bt"),
    # From MAC
    ("MAC", "NAV-M",  "英数/かな",   0,    "mac"),
    ("MAC", "SNAP-M", "Q",           0,    "mac"),
    ("MAC", "SYM",    "Space",       -18,  "mac"),
    ("MAC", "NUM",    "Enter",       -18,  "mac"),
    ("MAC", "MOUSE",  "ボール操作",  -18,  "mac"),
    ("MAC", "BLE",    "英数+かな",   -18,  "mac"),
    ("MAC", "PAN",    "P",           -18,  "mac"),
    ("MAC", "CURSOR", "Q",           -14,  "hidden"),  # CURSOR is unimplemented
    # From WIN
    ("WIN", "NAV-W",  "英数/かな",   0,    "win"),
    ("WIN", "SNAP-W", "Q",           0,    "win"),
    ("WIN", "SYM",    "Space",       +18,  "win"),
    ("WIN", "NUM",    "Enter",       +18,  "win"),
    ("WIN", "MOUSE",  "ボール操作",  +18,  "win"),
    ("WIN", "BLE",    "英数+かな",   +18,  "win"),
    ("WIN", "PAN",    "P",           +18,  "win"),
    ("WIN", "CURSOR", "Q",           +14,  "hidden"),  # CURSOR is unimplemented
    # O24 toggle (dashed, purple)
    ("MAC", "O24",    "Q+P",          0,   "o24"),
    ("WIN", "O24",    "Q+P",          0,   "o24"),
]

# ── Geometry helpers ─────────────────────────────────────────────────────────────

def box_port(name, tx, ty):
    """Return the point on node 'name' box edge facing toward (tx, ty)."""
    cx, cy = NODES[name]
    vx, vy = tx - cx, ty - cy
    hw, hh = NW / 2, NH / 2
    if vx == 0 and vy == 0:
        return cx, cy
    if abs(vx) * hh >= abs(vy) * hw and vx != 0:
        s = 1 if vx > 0 else -1
        return cx + hw * s, cy + vy * hw / abs(vx)
    else:
        s = 1 if vy > 0 else -1
        return cx + (vx * hh / abs(vy) if vy != 0 else 0), cy + hh * s


def quad_bezier(src, dst, offset):
    """Return (path_d, label_point) for a quadratic bezier arrow src→dst."""
    sx, sy = NODES[src]
    dx, dy = NODES[dst]
    p1 = box_port(src, dx, dy)
    p2 = box_port(dst, sx, sy)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    if offset:
        vx, vy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(vx, vy)
        if L > 0:
            mx += (-vy / L) * offset
            my += (vx / L) * offset
    path = f"M {p1[0]:.1f},{p1[1]:.1f} Q {mx:.1f},{my:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    lx = 0.25 * p1[0] + 0.5 * mx + 0.25 * p2[0]
    ly = 0.25 * p1[1] + 0.5 * my + 0.25 * p2[1]
    return path, (lx, ly)


# ── SVG helpers ──────────────────────────────────────────────────────────────────

def svg_text(x, y, s, size=9, bold=False, fill=C_TEXT, anchor="middle", readable=True):
    fw = "bold" if bold else "normal"
    stroke = ' stroke="white" stroke-width="3" paint-order="stroke"' if readable else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"'
            f' dominant-baseline="middle" font-family="{FONT}" font-size="{size}"'
            f' font-weight="{fw}" fill="{fill}"{stroke}>{s}</text>')


def arrow_marker(mid, col):
    return (
        f'<marker id="ah-{mid}" markerWidth="6" markerHeight="5"'
        f' refX="5.5" refY="2.5" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L6,2.5 L0,5 Z" fill="{col}"/></marker>'
    )


# ── Main builder ─────────────────────────────────────────────────────────────────

def build():
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    # defs
    out.append("<defs>")
    for mid, col in [("mac", MAC_C), ("win", WIN_C), ("bt", BT_C), ("o24", O24_C)]:
        out.append(arrow_marker(mid, col))
    out.append("</defs>")

    # background
    out.append(f'<rect width="{W}" height="{H}" fill="{C_BG}" rx="6"/>')

    # title
    out.append(svg_text(12, 20, "moNa2 — Layer Transition Diagram",
                        size=13, bold=True, fill=C_TEXT, anchor="start", readable=False))
    out.append(f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="{C_BOR}" stroke-width="1"/>')

    # zone labels  (no "Base" label — it overlaps with the BT arrow label)
    for lbl, lx, ly, col in [
        ("Shared layers (MAC &amp; WIN)", W // 2, 46, C_MUT),
        ("MAC-only",  130, 211, MAC_C),
        ("WIN-only",  730, 211, WIN_C),
        ("Snap gestures", 340, 376, C_MUT),
        ("Cursor / O24", 509, 445, C_MUT),
    ]:
        out.append(svg_text(lx, ly, lbl, size=9, fill=col, readable=False))

    # ── edges ──
    for src, dst, label, offset, kind in EDGES:
        col_map = {"mac": MAC_C, "win": WIN_C, "bt": BT_C, "o24": O24_C, "hidden": BT_C}
        col = col_map[kind]

        if kind == "bt":
            pa, (lxa, lya) = quad_bezier(src, dst, -9)
            pb, _ = quad_bezier(dst, src, -9)
            for p in (pa, pb):
                out.append(f'<path d="{p}" fill="none" stroke="{col}" stroke-width="1.2"'
                            f' opacity="0.65" marker-end="url(#ah-bt)"/>')
            lx = (NODES[src][0] + NODES[dst][0]) / 2
            ly = min(NODES[src][1], NODES[dst][1]) - 14
            out.append(svg_text(lx, ly, label, size=9, fill=col))
        elif kind == "hidden":
            path, (lx, ly) = quad_bezier(src, dst, offset)
            out.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="1.5"'
                       f' opacity="0" marker-end="url(#ah-mac)"/>')
            out.append(svg_text(lx, ly, label, size=9, fill=col, readable=False) \
                       .replace('>', ' opacity="0">', 1))
        elif kind == "o24":
            path, (lx, ly) = quad_bezier(src, dst, offset)
            out.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="1.5"'
                       f' opacity="0.75" stroke-dasharray="5 3" marker-end="url(#ah-o24)"/>')
            out.append(svg_text(lx, ly, label, size=9, fill=col))
        else:
            path, (lx, ly) = quad_bezier(src, dst, offset)
            out.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="1.5"'
                       f' opacity="0.75" marker-end="url(#ah-{kind})"/>')
            out.append(svg_text(lx, ly, label, size=9, fill=col))

    # ── nodes (drawn over edges) ──
    for name, (cx, cy) in NODES.items():
        col = LAYER_COLOR.get(name, C_MUT)
        x, y = cx - NW // 2, cy - NH // 2
        out.append(f'<rect x="{x}" y="{y}" width="{NW}" height="{NH}"'
                   f' rx="5" fill="{col}" stroke="white" stroke-width="2"/>')
        star = " ★" if name == "MAC" else ""
        out.append(svg_text(cx, cy, name + star, size=12, bold=True, fill="white",
                            readable=False))

    # ── legend ──
    ly = H - 14
    lx = 12
    for col, lbl in [
        (MAC_C, "MAC ベース時の遷移"),
        (WIN_C, "WIN ベース時の遷移"),
        (BT_C,  "BT profile 切替（双方向）"),
        (O24_C, "Q+P コンボ（トグル）"),
        (C_MUT, "★ = デフォルト層　キー離し = 元の層に復帰"),
    ]:
        out.append(f'<rect x="{lx}" y="{ly - 5}" width="16" height="3" rx="1" fill="{col}" opacity="0.8"/>')
        out.append(svg_text(lx + 20, ly, lbl, size=9, fill=C_MUT, anchor="start", readable=False))
        lx += len(lbl) * 6 + 34

    # outer border
    out.append(f'<rect width="{W}" height="{H}" fill="none" rx="6" stroke="{C_BOR}" stroke-width="1"/>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    svg = build()
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Written: {OUTPUT}")

if __name__ == "__main__":
    main()
