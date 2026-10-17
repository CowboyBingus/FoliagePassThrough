"""Foliage Pass-Through artwork: banner (the Nexus header format, 1300x372) and square cover.

    python art.py [folder]     (default: the assets folder above this one)

A tree and a bush in side view. A bomb fell straight through the tree's canopy, its dashed yellow trail running down
through the leaves, and explodes on the ground clear of the trunk; a rocket flew level through the bush and is still
going. The banner's header and the cover's side text say the same two things: explosives fly through leaves, trunks
still stop them. Everything is drawn from fixed numbers, so both PNGs re-render pixel for pixel."""
import math
import sys
from pathlib import Path

import style
from style import UI, UI_SEMI, Menu, Row, Spec, menu_panel, ui_size

SAYS = ('EXPLOSIVES FLY THROUGH LEAVES', 'TRUNKS STILL STOP THEM')
# Leaf clumps as (dx, dy, r) in canopy radii from the canopy's centre.
CANOPY = [(0.0, 0.0, 0.6), (-0.62, 0.22, 0.44), (0.62, 0.2, 0.46), (-0.36, -0.34, 0.46), (0.45, -0.36, 0.46),
          (0.0, -0.6, 0.38), (-0.95, 0.02, 0.32), (0.95, -0.02, 0.32)]
# The banner's wider canopy: one more clump each side, so at that size the bomb's path runs well inside the leaves.
CANOPY_WIDE = CANOPY + [(-1.3, 0.1, 0.36), (1.3, 0.1, 0.36)]
# The bush's tufts in bush radii from its centre, which sits 0.45 bush radii above the ground; a flat base fills
# below them, so the bush is low, wide and stands on the ground (unlike the round canopy).
BUSH = [(-1.0, 0.02, 0.42), (-0.55, -0.24, 0.48), (0.0, -0.36, 0.52), (0.55, -0.26, 0.48), (1.0, 0.0, 0.42)]
BUSH_HALF, BUSH_BASE = 1.2, 0.45     # half width of the flat base and its depth, in bush radii


def leaves(cv, cx, cy, radius, clumps, line_w):
    """One silhouette: light clumps under dark ones a line width smaller, so only the outer edge shows."""
    for dx, dy, r in clumps:
        cv.circle('paper', cx + dx * radius, cy + dy * radius, r * radius)
        cv.circle('dim', cx + dx * radius, cy + dy * radius, r * radius - line_w)


def bush(cv, cx, ground, radius, line_w):
    """The bush: tufts along the top over a flat base standing on the ground; returns its centre's y."""
    cy = ground - BUSH_BASE * radius
    half = BUSH_HALF * radius
    cv.rect('paper', cx - half, cy, cx + half, ground)
    cv.rect('dim', cx - half + line_w, cy, cx + half - line_w, ground - line_w)
    leaves(cv, cx, cy, radius, BUSH, line_w)
    return cy


def tree(cv, cx, ground, radius, line_w, clumps):
    """Trunk from the ground tapering to a blunt tip inside the canopy, two short limbs; returns the canopy centre's
    y."""
    cy = ground - 2.05 * radius
    trunk = 0.13 * radius
    cv.poly('cream', [(cx - trunk, ground), (cx + trunk, ground), (cx + trunk * 0.4, cy + 0.3 * radius),
                      (cx + trunk * 0.15, cy + 0.12 * radius), (cx - trunk * 0.15, cy + 0.12 * radius),
                      (cx - trunk * 0.4, cy + 0.3 * radius)])
    cv.line('cream', cx, cy + 0.85 * radius, cx - 0.36 * radius, cy + 0.3 * radius, trunk * 0.7)
    cv.line('cream', cx + 0.03 * radius, cy + 0.7 * radius, cx + 0.3 * radius, cy + 0.25 * radius, trunk * 0.6)
    leaves(cv, cx, cy, radius, clumps, line_w)
    return cy


def dashes(cv, x0, y0, x1, y1, width, dash, gap):
    """A dashed yellow line from (x0, y0) to (x1, y1), horizontal or vertical."""
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    t = 0.0
    while t < length:
        e = min(t + dash, length)
        cv.line('yellow', x0 + ux * t, y0 + uy * t, x0 + ux * e, y0 + uy * e, width)
        t += dash + gap


def bomb_outline(x, nose, length, width, grow=0.0):
    """A falling bomb's body pointing down, nose at `nose`: round nose, full belly, tapering to the tail. `grow`
    widens it all round (the gap cut around it in the explosion)."""
    belly, half = nose - 0.3 * length, width / 2 + grow
    pts = [(x + half * math.cos(math.pi * i / 12), belly + (0.3 * length + grow) * math.sin(math.pi * i / 12))
           for i in range(13)]                            # the round nose: right side, down round, left side
    narrow, end = 0.14 * width + grow, nose - length - grow
    return pts + [(x - half, nose - 0.55 * length), (x - narrow, end), (x + narrow, end), (x + half, nose - 0.55 * length)]


def bomb(cv, x, nose, length, width):
    """The bomb: cream body tapering to its tail, two yellow fins flaring from the tail with a box rim across them."""
    tail = nose - length
    cv.poly('cream', bomb_outline(x, nose, length, width))
    fin, rim = width * 0.6, 0.07 * length
    for side in (-1, 1):
        cv.poly('yellow', [(x + side * 0.2 * width, tail + 0.34 * length), (x + side * fin, tail + rim),
                           (x + side * fin, tail), (x + side * 0.14 * width, tail)])
    cv.rect('yellow', x - fin, tail, x + fin, tail + rim)


def explosion(cv, x, ground, r, spikes=7):
    """A filled yellow starburst standing on the ground: spikes fanning up from where the bomb's nose hits."""
    pts = [(x - r * 0.62, ground)]
    for i in range(2 * spikes + 1):
        a = math.pi * (1 + i / (2 * spikes))              # ground to ground across the top
        reach = r if i % 2 else 0.52 * r
        pts.append((x + reach * math.cos(a), ground + reach * math.sin(a)))
    pts.append((x + r * 0.62, ground))
    cv.poly('yellow', pts)


def rocket(cv, tail, y, length, width):
    """A rocket flying right, its tail at `tail`: cream body with a pointed nose, yellow fins."""
    body = tail + 0.78 * length
    cv.poly('cream', [(tail, y - width / 2), (body, y - width / 2), (tail + length, y), (body, y + width / 2),
                      (tail, y + width / 2)])
    fin = 0.3 * length
    cv.poly('yellow', [(tail + fin, y - width / 2), (tail, y - width * 0.95), (tail, y - width / 2)])
    cv.poly('yellow', [(tail + fin, y + width / 2), (tail, y + width * 0.95), (tail, y + width / 2)])


def scene(cv, x0, x1, top, ground, line_w, cap, sky, bush_size=0.5, spread=1.0, drop=0.78, lead=0.2, blast=0.44,
          canopy=CANOPY, scale=1.0):
    """The tree (left) with the bomb, the bush (right) with the rocket, on one ground line from x0 to x1. The bomb's
    trail starts at `sky` and falls `drop` canopy radii right of the trunk into an explosion reaching `blast` radii;
    the rocket's trail starts `lead` radii right of the explosion. The bush is `bush_size` canopy radii and sits
    `spread` of the way from its nearest place (a short lead-in of the rocket's trail) to its farthest (the rocket's
    nose on x1). `scale` enlarges the bomb and the rocket, for small formats."""
    cv.rect('dim', x0, ground, x1, ground + line_w)
    radius = (ground - top) / 3.0
    left, right = (max(sign * dx + r for dx, _, r in canopy) for sign in (-1, 1))   # the canopy's reach each side
    cx = x0 + (left + 0.08) * radius
    cy = tree(cv, cx, ground, radius, line_w, canopy)
    drop_x = cx + drop * radius                      # through the canopy, clear of the trunk and both limbs
    assert right - drop >= 0.45, 'the bomb would only graze the canopy'
    blast *= radius                                  # the explosion's reach, at least 0.2 radii clear of the trunk
    assert drop * radius - blast >= 0.33 * radius, 'the explosion would touch the trunk'
    length, width = 0.7 * scale * radius, 0.25 * scale * radius
    nose = ground - 0.1 * radius
    dash, gap = line_w * 5, line_w * 3.2
    dashes(cv, drop_x, sky, drop_x, nose - length - 0.1 * radius, line_w * 1.6, dash, gap)
    explosion(cv, drop_x, ground, blast)
    cv.poly('yellow', bomb_outline(drop_x, nose, length, width, grow=1.6 * line_w), fill=0)   # a dark gap round it
    bomb(cv, drop_x, nose, length, width)

    bush_r, rocket_len = bush_size * radius, 0.48 * scale * radius
    clear = drop_x + blast + lead * radius           # the rocket's trail starts right of the explosion
    reach = max(BUSH_HALF, *(dx + r for dx, _, r in BUSH)) * bush_r     # the bush's half width, outer tufts included
    out = 0.4 * bush_r                               # the trail between the bush and the rocket's tail
    near, far = clear + 0.7 * bush_r + reach, x1 - reach - out - rocket_len
    assert near <= far, ('the bush and rocket do not fit', near, far)
    bx = near + spread * (far - near)
    by = bush(cv, bx, ground, bush_r, line_w)
    level = by - 0.15 * bush_r                       # high enough that the rocket's fins clear the ground
    tail = bx + reach + out                          # out of the bush on the far side, still flying
    dashes(cv, clear, level, tail - 0.1 * out, level, line_w * 1.6, dash, gap)
    rocket(cv, tail, level, rocket_len, 0.16 * scale * radius)

    size = ui_size(cap)
    cv.text('gray', cx + right * radius + 1.2 * cap, cy + cap / 2, 'LEAVES', UI, size, UI_SEMI, tracking=0.1)
    cv.text('gray', cx - 0.13 * radius - 1.5 * cap, ground - 0.3 * radius, 'TRUNK', UI, size, UI_SEMI, tracking=0.1,
            anchor='right')
    cv.text('gray', bx, by - 0.88 * bush_r - cap * 0.7, 'BUSH', UI, size, UI_SEMI, tracking=0.1, anchor='center')


def menu(cv, g: Menu) -> None:
    """The banner's panel: the two sentences on one header line, the scene below it, all above Nexus's overlay."""
    menu_panel(cv, g)
    base = g.cap_top + 14                       # level with the title's first line, as the siblings' headers
    size = ui_size(11)
    _, right = cv.text('gray', g.x0, base, SAYS[0], UI, size, UI_SEMI, tracking=0.09)
    cv.circle('yellow', right + 9, base - 11 / 2, 2.2)
    _, end = cv.text('gray', right + 18, base, SAYS[1], UI, size, UI_SEMI, tracking=0.09)
    assert end <= g.x1, ('header too wide', end, g.x1)
    # At this size the cover's proportions crowd the bomb against the trunk and shrink the action to specks: a wider
    # canopy keeps the bomb's path well inside the leaves and its explosion clear of the trunk, the bomb and rocket
    # are drawn larger, and the rocket's trail starts a clear stretch after the explosion.
    scene(cv, g.x0 + 36, g.x1, base + 20, base + 134, 2, 11, sky=base + 18, bush_size=0.85, spread=0.8, drop=1.05,
          lead=1.1, blast=0.53, canopy=CANOPY_WIDE, scale=1.6)


def cover_row(cv, r: Row) -> None:
    """The panel above the title: it bleeds off the right edge and ends above the title's first line."""
    panel_x, corner = r.x0 - 24, 30
    top, bottom = r.top + 40, r.top + r.h
    cv.poly('panel', [(panel_x + corner, top), (cv.width, top), (cv.width, bottom), (panel_x, bottom),
                      (panel_x, top + corner)])
    cv.polyline('edge', [(cv.width, bottom), (panel_x, bottom), (panel_x, top + corner), (panel_x + corner, top),
                         (cv.width, top)], 2)
    cv.line('yellow', panel_x, top + corner, panel_x + corner, top, 3.5)
    scene(cv, r.x0 + 24, r.x1, top + 130, bottom - 64, 3.5, 20, sky=top + 60, bush_size=0.38, spread=1.0)


SPEC = Spec(wide='FOLIAGE', bar='PASS-THROUGH', square=['FOLIAGE'], menu=menu, cover_row=cover_row,
            caption=list(SAYS), caption_line=0, cover_layout='bottom', menu_x0=827)

if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    style.nexus(SPEC, out / 'banner.png')
    style.cover(SPEC, out / 'thumbnail.png')
    print(out)
