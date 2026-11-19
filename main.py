#!/usr/bin/env python3
"""The World in One Page -- 19 November 2026.

A pure-stdlib front-page infographic. Hand-built vector stroke font,
from-scratch PNG encoder (zlib only), no network, no models, no fonts
from disk. Deterministic: the same bytes on every run.

Run:  python3 main.py        -> writes /output/entry.png
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# Glyphs are polylines on a 7 x 12 grid (x 0..6, y 0..11).
# Capitals sit on y 0..9; lower-case x-height is y 4..9, ascenders reach
# y 0, descenders reach y 11. Fixed advance: 8 units per character.
# Each glyph: list of strokes; each stroke: list of (x, y) points.

FONT = {
    "A": [[(0, 9), (3, 0), (6, 9)], [(2, 6), (4, 6)]],
    "B": [[(0, 0), (0, 9)], [(0, 0), (4, 0), (5, 1), (5, 3), (4, 4), (0, 4)],
          [(0, 4), (4, 4), (5, 5), (5, 8), (4, 9), (0, 9)]],
    "C": [[(6, 2), (5, 0), (2, 0), (0, 2), (0, 7), (2, 9), (5, 9), (6, 7)]],
    "D": [[(0, 0), (0, 9)], [(0, 0), (4, 0), (6, 2), (6, 7), (4, 9), (0, 9)]],
    "E": [[(0, 0), (0, 9)], [(0, 0), (5, 0)], [(0, 4), (4, 4)], [(0, 9), (5, 9)]],
    "F": [[(0, 0), (0, 9)], [(0, 0), (5, 0)], [(0, 4), (4, 4)]],
    "G": [[(6, 2), (5, 0), (2, 0), (0, 2), (0, 7), (2, 9), (5, 9), (6, 7), (6, 5), (3, 5)]],
    "H": [[(0, 0), (0, 9)], [(6, 0), (6, 9)], [(0, 5), (6, 5)]],
    "I": [[(1, 0), (5, 0)], [(3, 0), (3, 9)], [(1, 9), (5, 9)]],
    "J": [[(1, 0), (5, 0)], [(4, 0), (4, 8), (3, 9), (1, 9), (0, 7)]],
    "K": [[(0, 0), (0, 9)], [(5, 0), (0, 5)], [(2, 6), (5, 9)]],
    "L": [[(0, 0), (0, 9)], [(0, 9), (5, 9)]],
    "M": [[(0, 9), (0, 0), (3, 5), (6, 0), (6, 9)]],
    "N": [[(0, 9), (0, 0), (6, 9), (6, 0)]],
    "O": [[(2, 0), (4, 0), (6, 2), (6, 7), (4, 9), (2, 9), (0, 7), (0, 2), (2, 0)]],
    "P": [[(0, 0), (0, 9)], [(0, 0), (4, 0), (6, 2), (6, 3), (4, 5), (0, 5)]],
    "Q": [[(2, 0), (4, 0), (6, 2), (6, 7), (4, 9), (2, 9), (0, 7), (0, 2), (2, 0)],
          [(3, 6), (6, 10)]],
    "R": [[(0, 0), (0, 9)], [(0, 0), (4, 0), (6, 2), (6, 3), (4, 5), (0, 5)],
          [(3, 5), (6, 9)]],
    "S": [[(6, 2), (5, 0), (2, 0), (0, 2), (1, 4), (5, 5), (6, 7), (5, 9), (2, 9), (0, 7)]],
    "T": [[(0, 0), (6, 0)], [(3, 0), (3, 9)]],
    "U": [[(0, 0), (0, 7), (2, 9), (4, 9), (6, 7), (6, 0)]],
    "V": [[(0, 0), (3, 9), (6, 0)]],
    "W": [[(0, 0), (2, 9), (3, 6), (4, 9), (6, 0)]],
    "X": [[(0, 0), (6, 9)], [(6, 0), (0, 9)]],
    "Y": [[(0, 0), (3, 5), (6, 0)], [(3, 5), (3, 9)]],
    "Z": [[(0, 0), (6, 0), (0, 9), (6, 9)]],
    "a": [[(1, 6), (2, 4), (4, 4), (6, 6), (6, 8), (4, 9), (2, 9), (1, 7)], [(6, 4), (6, 9)]],
    "b": [[(1, 0), (1, 9)], [(1, 5), (4, 4), (6, 6), (6, 8), (4, 9), (1, 9)]],
    "c": [[(6, 5), (5, 4), (2, 4), (1, 6), (1, 8), (2, 9), (5, 9), (6, 8)]],
    "d": [[(5, 0), (5, 9)], [(5, 5), (2, 4), (1, 6), (1, 8), (2, 9), (5, 9)]],
    "e": [[(6, 5), (5, 4), (2, 4), (1, 6), (1, 8), (2, 9), (5, 9), (6, 7)],
          [(1, 6), (6, 6)]],
    "f": [[(5, 0), (3, 0), (2, 1), (2, 9)], [(1, 4), (4, 4)]],
    "g": [[(1, 6), (2, 4), (4, 4), (5, 6), (5, 8), (4, 9), (2, 9), (1, 7)],
          [(5, 9), (4, 11), (2, 11), (1, 10)]],
    "h": [[(1, 0), (1, 9)], [(1, 5), (3, 4), (5, 5), (6, 7), (6, 9)]],
    "i": [[(3, 4), (3, 9)], [(3, 1), (3, 2)]],
    "j": [[(4, 4), (4, 10), (3, 11), (2, 11)], [(4, 1), (4, 2)]],
    "k": [[(1, 0), (1, 9)], [(5, 4), (1, 7)], [(3, 6), (5, 9)]],
    "l": [[(3, 0), (3, 9)]],
    "m": [[(1, 9), (1, 4), (3, 4), (4, 6), (4, 9)], [(4, 4), (5, 4), (6, 6), (6, 9)]],
    "n": [[(1, 4), (1, 9)], [(1, 4), (3, 4), (5, 5), (6, 7), (6, 9)]],
    "o": [[(2, 4), (4, 4), (6, 6), (6, 8), (4, 9), (2, 9), (0, 7), (0, 6), (2, 4)]],
    "p": [[(1, 4), (1, 11)], [(1, 5), (4, 4), (6, 6), (6, 8), (4, 9), (1, 9)]],
    "q": [[(5, 4), (5, 11)], [(5, 5), (2, 4), (1, 6), (1, 8), (2, 9), (5, 9)]],
    "r": [[(1, 4), (1, 9)], [(1, 4), (3, 4), (5, 5), (6, 6)]],
    "s": [[(6, 5), (5, 4), (2, 4), (1, 5), (1, 6), (2, 7), (5, 7), (6, 8), (5, 9), (2, 9), (1, 8)]],
    "t": [[(3, 0), (3, 9)], [(1, 4), (4, 4)], [(2, 9), (4, 9)]],
    "u": [[(1, 4), (1, 8), (2, 9), (4, 9), (6, 8), (6, 4)]],
    "v": [[(0, 4), (3, 9), (6, 4)]],
    "w": [[(0, 4), (1, 9), (3, 6), (5, 9), (6, 4)]],
    "x": [[(0, 4), (6, 9)], [(6, 4), (0, 9)]],
    "y": [[(0, 4), (3, 9), (6, 4)], [(3, 9), (2, 11)]],
    "z": [[(0, 4), (6, 4), (0, 9), (6, 9)]],
    "0": [[(2, 0), (4, 0), (6, 2), (6, 7), (4, 9), (2, 9), (0, 7), (0, 2), (2, 0)]],
    "1": [[(1, 2), (3, 0)], [(3, 0), (3, 9)], [(1, 9), (5, 9)]],
    "2": [[(0, 2), (1, 0), (4, 0), (6, 2), (6, 4), (0, 9), (6, 9)]],
    "3": [[(1, 0), (4, 0), (6, 2), (6, 4), (4, 5), (1, 5)],
          [(4, 5), (6, 6), (6, 8), (4, 9), (1, 9), (0, 7)]],
    "4": [[(5, 0), (0, 6), (5, 6)], [(4, 0), (4, 9)]],
    "5": [[(6, 0), (0, 0), (0, 4), (4, 4), (6, 6), (6, 8), (4, 9), (1, 9), (0, 8)]],
    "6": [[(5, 0), (2, 0), (0, 2), (0, 8), (2, 9), (5, 9), (6, 7), (6, 5), (4, 4), (1, 4)]],
    "7": [[(0, 0), (6, 0), (3, 9)]],
    "8": [[(2, 0), (4, 0), (6, 2), (6, 4), (4, 5), (2, 5), (0, 4), (0, 2), (2, 0)],
          [(2, 5), (4, 5), (6, 7), (6, 8), (4, 9), (2, 9), (0, 7), (0, 6), (2, 5)]],
    "9": [[(6, 8), (6, 2), (5, 0), (2, 0), (0, 2), (0, 4), (2, 5), (5, 5), (6, 4)],
          [(6, 4), (6, 9)]],
    " ": [],
    ".": [[(3, 8), (3, 9)]],
    ",": [[(3, 8), (3, 9)], [(3, 9), (2, 11)]],
    ":": [[(3, 2), (3, 3)], [(3, 7), (3, 8)]],
    ";": [[(3, 2), (3, 3)], [(3, 7), (3, 8)], [(3, 8), (2, 10)]],
    "!": [[(3, 0), (3, 6)], [(3, 8), (3, 9)]],
    "?": [[(1, 2), (2, 0), (4, 0), (6, 2), (6, 3), (4, 5), (3, 6), (3, 7)],
          [(3, 8), (3, 9)]],
    "'": [[(3, 0), (2, 3)]],
    '"': [[(2, 0), (2, 2)], [(4, 0), (4, 2)]],
    "-": [[(1, 5), (5, 5)]],
    "(": [[(4, 0), (2, 2), (2, 7), (4, 9)]],
    ")": [[(2, 0), (4, 2), (4, 7), (2, 9)]],
    "/": [[(5, 0), (1, 9)]],
    "%": [[(0, 0), (6, 9)], [(1, 1), (2, 1), (2, 3), (1, 3), (1, 1)],
          [(4, 6), (5, 6), (5, 8), (4, 8), (4, 6)]],
    "$": [[(5, 1), (4, 0), (2, 0), (0, 2), (1, 4), (5, 5), (6, 7), (5, 9), (2, 9), (0, 8)],
          [(3, 0), (3, 9)]],
    "+": [[(3, 1), (3, 8)], [(1, 4), (5, 4)]],
    "=": [[(1, 3), (5, 3)], [(1, 6), (5, 6)]],
    "*": [[(3, 0), (3, 6)], [(0, 2), (6, 4)], [(6, 2), (0, 4)]],
    "[": [[(4, 0), (1, 0), (1, 9), (4, 9)]],
    "]": [[(2, 0), (5, 0), (5, 9), (2, 9)]],
    "_": [[(0, 9), (6, 9)]],
    "&": [[(5, 4), (4, 4), (2, 5), (1, 7), (2, 9), (5, 9), (6, 8), (5, 6), (2, 3), (1, 1), (2, 0), (4, 0), (5, 1)]],
}

ADVANCE = 8          # font units per character (fixed-width)
CELL_H = 12          # font units per line (includes descender room)


def text_width_units(text):
    return len(text) * ADVANCE


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg) * (w * h)

    def _px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:(x1 - x0) * 3 + i] = color * (x1 - x0)

    def disc(self, cx, cy, r, color):
        r2 = r * r
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int((r2 - dy * dy) ** 0.5)
            for xx in range(cx - dx, cx + dx + 1):
                self._px(xx, yy, color)

    def line(self, x0, y0, x1, y1, width, color):
        """Thick line with round caps, drawn as stamped discs."""
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = max(1, width // 2)
        for s in range(steps + 1):
            t = s / steps
            self.disc(int(round(x0 + dx * t)), int(round(y0 + dy * t)), r, color)

    def poly(self, pts, width, color):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], width, color)

    def circle(self, cx, cy, r, width, color):
        # 48-gon outline
        import math
        pts = [(cx + int(round(r * math.cos(a))), cy + int(round(r * math.sin(a))))
               for a in (i * 2 * math.pi / 48 for i in range(49))]
        self.poly(pts, width, color)

    # ------------------------------------------------------------ text
    def _glyph(self, ch, x, y, scale, width, color):
        strokes = FONT.get(ch)
        if strokes is None:
            ch = "?"
            strokes = FONT["?"]
        lw = max(1, int(round(scale * 1.05)))
        for stroke in strokes:
            pts = [(x + int(round(px * scale)), y + int(round(py * scale)))
                   for px, py in stroke]
            if len(pts) == 1:
                self.disc(pts[0][0], pts[0][1], max(1, lw // 2), color)
            else:
                self.poly(pts, lw, color)

    def text(self, x, y, s, scale, color, bold=False):
        """Draw text; (x, y) is the top-left of the first glyph cell."""
        cx = x
        for ch in s:
            self._glyph(ch, cx, y, scale, 0, color)
            if bold:
                self._glyph(ch, cx + 1, y, scale, 0, color)
            cx += int(round(ADVANCE * scale))
        return cx

    def text_w(self, s, scale):
        return int(round(len(s) * ADVANCE * scale))

    def text_center(self, cx, y, s, scale, color, bold=False):
        self.text(cx - self.text_w(s, scale) // 2, y, s, scale, color, bold)

    def wrap(self, s, scale, max_w):
        """Greedy word wrap; returns list of lines that fit max_w px."""
        max_chars = max(1, int(max_w // round(ADVANCE * scale)))
        words, lines, cur = s.split(" "), [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                # hard-split overlong words
                while len(wd) > max_chars:
                    lines.append(wd[:max_chars])
                    wd = wd[max_chars:]
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, scale, color, max_w, leading=None):
        lh = leading if leading is not None else int(round(CELL_H * scale * 1.25))
        for line in self.wrap(s, scale, max_w):
            self.text(x, y, line, scale, color)
            y += lh
        return y


# ---------------------------------------------------------------- png
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def save_png(canvas, path):
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    row_bytes = canvas.w * 3
    for yy in range(canvas.h):
        raw.append(0)
        raw += canvas.buf[yy * row_bytes:(yy + 1) * row_bytes]
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
           _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- palette
PAPER = bytes((248, 244, 236))
INK = bytes((20, 20, 20))
RED = bytes((178, 34, 34))
BLUE = bytes((30, 80, 160))
GOLD = bytes((198, 148, 28))
GRAY = bytes((112, 110, 102))
SUN = bytes((255, 215, 106))
SKY = [(43, 26, 74), (90, 32, 90), (160, 44, 90), (220, 80, 60),
       (240, 130, 50), (250, 190, 90)]

# ---------------------------------------------------------------- content
# Verified from live sources on 19 Nov 2026 (all dated 18-19 Nov):
#  GTA VI  - Reuters / AP / BBC via TBS News, NorthJersey, Stocktwits
#  Gulf    - Reuters / AP via titobaronmedia, farazwire, Reuters
#  Jeffries- NPR / CNN / USA Today / NY Post
#  Akvan   - India Meteorological Department via The Hindu / Daily Jagran
#  Voyager - Reuters / NASA
#  EU loan - Reuters
#  Ticker  - Pew Research Center; AP; Reuters
MASTHEAD = "THE WORLD IN ONE PAGE"
DATE_LINE = "THURSDAY 19 NOVEMBER 2026"
TAGLINE = "ONE DAY. ONE IMAGE. EVERYTHING THAT MATTERED."

LEAD_KICKER = "CULTURE - GAMING"
LEAD_HEAD = ["AFTER 13 YEARS,", "VICE CITY OPENS"]
LEAD_BODY = ("Grand Theft Auto VI rolls out worldwide at midnight local "
             "time, ending the longest wait in gaming. New Zealand played first.")
LEAD_FACTS = "16M PREORDERS - $1.5BN - METACRITIC 99 - $79.99"

GULF_KICKER = "THE GULF"
GULF_HEAD = ["U.S. AND IRAN", "TRADE FIRE"]
GULF_BODY = ("U.S. jets hit a missile site on Iran's Qeshm Island. Hours "
             "later Iran fired on a U.S. base in Kuwait and struck Bahrain again.")

SPEAKER_KICKER = "WASHINGTON"
SPEAKER_HEAD = ["JEFFRIES", "FOR SPEAKER"]
SPEAKER_BODY = ("House Democrats picked Hakeem Jeffries 251-11. The full "
                "House votes Jan. 3; if he wins, he is the first Black "
                "Speaker in U.S. history.")

AKVAN_KICKER = "WEATHER"
AKVAN_HEAD = ["CYCLONE AKVAN", "NEARS INDIA"]
AKVAN_BODY = ("Severe storm Akvan nears India's east coast, due ashore "
              "Friday noon with 100 km/h winds.")

VOYAGER_KICKER = "SPACE"
VOYAGER_HEAD = ["VOYAGER 1, ONE", "LIGHT-DAY OUT"]
VOYAGER_BODY = ("NASA's 1977 probe is 16 billion miles out. A radio signal "
                "now takes a full day to reach it.")

EU_KICKER = "EUROPE"
EU_HEAD = ["EU OFFERS KYIV", "45BN EUROS"]
EU_BODY = ("Brussels proposed a 45-billion-euro loan to cover two-thirds "
           "of Ukraine's 2027 gap.")

TICKER = [
    "PEW: ISLAM TO PASS CHRISTIANITY BY 2035  -  TRUMP, XI AND PUTIN MEET IN SHENZHEN",
    "FED POINTS TO MORE HIKES  -  AUSTRALIA SANCTIONS SETTLERS  -  DUCKETT 133 LEADS ENGLAND",
]
FOOTER = "SOURCES: REUTERS - AP - BBC - NPR - CNN - NASA - IMD - PEW RESEARCH - 19 NOV 2026"
BUILT = "BUILT WITH PYTHON 3.13, STANDARD LIBRARY ONLY - NO MODELS, NO NETWORK"


def rule(c, x, y, w, t, color=INK):
    c.rect(x, y, w, t, color)


def draw_art_panel(c, x, y, w, h):
    """Sunset over Vice City: stepped sky, sun, skyline, giant VI."""
    band = h // len(SKY)
    for i, col in enumerate(SKY):
        c.rect(x, y + i * band, w, band + 1, bytes(col))
    cx = x + w // 2
    c.disc(cx, y + 128, 40, SUN)
    # skyline silhouettes
    heights = [58, 84, 46, 96, 70, 110, 52, 88, 64, 100, 44, 76, 60, 92, 50]
    bw = w // len(heights)
    base = y + h
    for i, hh in enumerate(heights):
        c.rect(x + i * bw, base - hh, bw - 3, hh, INK)
    c.text(cx - c.text_w("VI", 9.0) // 2, y + 14, "VI", 9.0, PAPER, bold=True)
    c.text(cx - c.text_w("LEONIDA - VICE CITY", 1.5) // 2, base - 26,
           "LEONIDA - VICE CITY", 1.5, PAPER)


def story_block(c, x, y, w, kicker, kcolor, head, head_scale, body, body_scale):
    c.text(x, y, kicker, 1.7, kcolor, bold=True)
    hy = y + 26
    lh = int(round(CELL_H * head_scale * 1.15))
    for line in head:
        c.text(x, hy, line, head_scale, INK, bold=True)
        hy += lh
    by = hy + 6
    c.para(x, by, body, body_scale, INK, w,
           leading=int(round(CELL_H * body_scale * 1.22)))
    return by


def build():
    c = Canvas(W, H, PAPER)
    # outer frame
    c.rect(12, 12, 1000, 2, INK)
    c.rect(12, 1010, 1000, 2, INK)
    c.rect(12, 12, 2, 1000, INK)
    c.rect(1010, 12, 2, 1000, INK)

    # ---- masthead
    c.text_center(512, 40, MASTHEAD, 5.0, INK, bold=True)
    c.text_center(512, 98, DATE_LINE, 3.0, RED, bold=True)
    c.text_center(512, 134, TAGLINE, 1.6, GRAY)
    rule(c, 28, 158, 968, 3)

    # ---- lead story
    c.text(28, 172, LEAD_KICKER, 1.8, RED, bold=True)
    hy = 198
    for line in LEAD_HEAD:
        c.text(28, hy, line, 4.6, INK, bold=True)
        hy += 60
    c.para(28, 324, LEAD_BODY, 1.7, INK, 608, leading=25)
    c.text(28, 404, LEAD_FACTS, 1.5, BLUE, bold=True)
    draw_art_panel(c, 656, 172, 340, 252)
    rule(c, 28, 440, 968, 2)

    # ---- middle row: two columns
    story_block(c, 28, 452, 468, GULF_KICKER, RED, GULF_HEAD, 3.2, GULF_BODY, 1.6)
    story_block(c, 528, 452, 468, SPEAKER_KICKER, BLUE, SPEAKER_HEAD, 3.2,
                SPEAKER_BODY, 1.6)
    c.rect(512, 452, 2, 210, INK)
    rule(c, 28, 678, 968, 2)

    # ---- bottom row: three columns
    cols = [
        (28, AKVAN_KICKER, RED, AKVAN_HEAD, AKVAN_BODY),
        (359, VOYAGER_KICKER, BLUE, VOYAGER_HEAD, VOYAGER_BODY),
        (690, EU_KICKER, GOLD, EU_HEAD, EU_BODY),
    ]
    for x, kicker, kcolor, head, body in cols:
        c.rect(x, 692, 40, 5, kcolor)
        story_block(c, x, 706, 306, kicker, kcolor, head, 2.4, body, 1.5)

    # ---- ticker
    c.rect(28, 886, 968, 58, INK)
    c.text(44, 894, TICKER[0], 1.25, PAPER)
    c.text(44, 918, TICKER[1], 1.25, PAPER)

    # ---- footer
    c.text_center(512, 956, FOOTER, 1.3, GRAY)
    c.text_center(512, 978, BUILT, 1.3, GRAY)
    return c


def main():
    out = os.environ.get("OUTPUT", "/output/entry.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    size = save_png(build(), out)
    print("wrote %s (%d bytes)" % (out, size))


if __name__ == "__main__":
    main()
