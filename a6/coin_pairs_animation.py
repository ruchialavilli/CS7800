"""
Oblivious heavy-coin weighing when 3^(w-1) < n < 3^w.

Each coin gets a signature column in {-1, 0, +1}^w: +1 = left pan in that
weighing, -1 = right pan, 0 = sits out. Weighing j measures

    left - right = g * (row j sum) + delta * (heavy coin's entry in row j)

so the scale reads the heavy coin's signature only if every row sums to 0.
With fewer than 3^w coins we can't use every signature, so we pick columns in
cancelling pairs v, -v (plus the all-zero column when n is odd).

coin_pairs_n7.gif   n = 7, w = 2: naive pick fails, build by pairs + zero
                    column, then run the fixed weighings twice.
coin_pairs_n6.gif   n = 6, w = 2: same, but n is even so no zero column.

Requires Pillow.
"""

import itertools
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1040, 580
BG, FG, MUTED, RULE = "#f7f8fa", "#1b2330", "#6b7685", "#c9d1dc"
BLUE, BLUE_SOFT = "#2f5bd3", "#dbe4fa"
GREEN, GREEN_SOFT = "#2e8b57", "#d6efe0"
AMBER, AMBER_SOFT = "#b7791f", "#fbedd0"
RED, RED_SOFT = "#c23d2a", "#f8dcd7"

G, HEAVY = 10, 11                     # genuine weight, heavy weight (delta < g)
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def font(size, bold=False):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size, index=1 if bold else 0)
    except OSError:
        return ImageFont.load_default(size=size)


F_TITLE, F_BIG, F, F_SMALL = font(22, True), font(20), font(16), font(13)


def sign(x):
    return (x > 0) - (x < 0)


def fmt(v):
    return "0" if v == 0 else f"{v:+d}"


def vec(v):
    return "(" + ", ".join(fmt(x) for x in v) + ")"


def pair_columns(n, w):
    """n distinct columns, every row summing to 0: pairs v, -v, plus the zero column if n is odd."""
    assert n <= 3 ** w
    reps = [v for v in itertools.product((1, 0, -1), repeat=w)
            if any(v) and next(x for x in v if x) == 1]
    reps.sort(key=lambda v: sum(map(abs, v)))
    cols = []
    for v in reps[: n // 2]:          # (3^w - 1)/2 reps available, and n//2 <= that
        cols += [v, tuple(-x for x in v)]
    if n % 2:
        cols.append((0,) * w)
    return cols


def weigh(cols, j, heavy):
    left = [i for i, c in enumerate(cols) if c[j] == 1]
    right = [i for i, c in enumerate(cols) if c[j] == -1]
    out = [i for i, c in enumerate(cols) if c[j] == 0]
    wt = lambda idx: sum(HEAVY if i == heavy else G for i in idx)
    return left, right, out, sign(wt(left) - wt(right))


# ---------- drawing ----------

MX, MY, CW, CH = 40, 150, 46, 40


def coin(d, x, y, label, hl=False):
    d.ellipse([x - 15, y - 15, x + 15, y + 15], fill=GREEN_SOFT if hl else "#ffffff",
              outline=GREEN if hl else FG, width=2)
    d.text((x, y), label, font=F, fill=GREEN if hl else FG, anchor="mm")


def draw_matrix(d, cols, n, w, row=None, col=None, new=()):
    for i in range(n):
        x = MX + 90 + i * (CW + 4)
        d.text((x + CW / 2, MY - 18), LETTERS[i], font=F, fill=GREEN if i == col else FG, anchor="mm")
    for j in range(w):
        y = MY + j * (CH + 6)
        d.text((MX, y + CH / 2), f"weigh {j + 1}", font=F_SMALL, fill=BLUE if j == row else MUTED, anchor="lm")
        for i in range(n):
            x = MX + 90 + i * (CW + 4)
            if i >= len(cols):
                d.rounded_rectangle([x, y, x + CW, y + CH], radius=5, fill=BG, outline=RULE, width=1)
                continue
            v = cols[i][j]
            fill = {1: BLUE_SOFT, -1: AMBER_SOFT, 0: "#ffffff"}[v]
            d.rounded_rectangle([x, y, x + CW, y + CH], radius=5, fill=fill,
                                outline=BLUE if i in new else RULE, width=3 if i in new else 1)
            d.text((x + CW / 2, y + CH / 2), fmt(v), font=F, fill=FG if v else MUTED, anchor="mm")
        if cols:
            s = sum(c[j] for c in cols)
            d.text((MX + 100 + n * (CW + 4), y + CH / 2), f"sum = {s}", font=F,
                   fill=GREEN if s == 0 else RED, anchor="lm")
    if row is not None:
        y = MY + row * (CH + 6)
        d.rounded_rectangle([MX + 84, y - 4, MX + 86 + n * (CW + 4), y + CH + 4], radius=7, outline=BLUE, width=2)
    if col is not None:
        x = MX + 90 + col * (CW + 4)
        d.rounded_rectangle([x - 4, MY - 34, x + CW + 4, MY + w * (CH + 6)], radius=7, outline=GREEN, width=3)
    # legend
    ly = MY + w * (CH + 6) + 16
    for k, (fill, txt) in enumerate([(BLUE_SOFT, "+1 left pan"), (AMBER_SOFT, "-1 right pan"),
                                     ("#ffffff", "0 sits out")]):
        lx = MX + k * 150
        d.rounded_rectangle([lx, ly, lx + 16, ly + 16], radius=3, fill=fill, outline=RULE)
        d.text((lx + 24, ly + 8), txt, font=F_SMALL, fill=MUTED, anchor="lm")


def draw_scale(d, cols, j, heavy, reveal=False):
    left, right, out, tip = weigh(cols, j, heavy)
    cx, cy, L = 820, 210, 140
    th = math.radians(10) * tip       # tip = +1 → left end goes down
    d.polygon([(cx, cy), (cx - 12, cy + 18), (cx + 12, cy + 18)], fill=FG)
    d.line([cx, cy + 18, cx, cy + 200], fill=FG, width=4)
    d.line([cx - 60, cy + 200, cx + 60, cy + 200], fill=FG, width=5)
    ends = [(cx - L * math.cos(th), cy + L * math.sin(th), left),
            (cx + L * math.cos(th), cy - L * math.sin(th), right)]
    d.line([ends[0][0], ends[0][1], ends[1][0], ends[1][1]], fill=FG, width=5)
    for ex, ey, idx in ends:
        py = ey + 80
        d.line([ex, ey, ex - 58, py], fill=MUTED, width=1)
        d.line([ex, ey, ex + 58, py], fill=MUTED, width=1)
        d.chord([ex - 65, py - 14, ex + 65, py + 14], 0, 180, fill="#e6e9ee", outline=FG, width=2)
        for k, i in enumerate(idx):
            r, c = divmod(k, 4)
            m = min(4, len(idx) - r * 4)
            coin(d, ex + (c - (m - 1) / 2) * 32, py - 16 - r * 32, LETTERS[i], reveal and i == heavy)
    ty = cy + 240
    d.text((cx - 190, ty), "sitting out:", font=F_SMALL, fill=MUTED, anchor="lm")
    for k, i in enumerate(out):
        coin(d, cx - 60 + k * 36, ty, LETTERS[i], reveal and i == heavy)
    word = {1: "left side down → +1", -1: "right side down → -1", 0: "balanced → 0"}[tip]
    d.text((cx, cy - 50), f"weighing {j + 1}: {word}", font=F, fill=BLUE, anchor="mm")
    return left, right, tip


def frame(n, w, title, sub, cols=(), row=None, col=None, new=(), scale=None, reading=None,
          status="", status_color=FG, secret=None):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((40, 22), title, font=F_TITLE, fill=FG)
    d.text((40, 56), sub, font=F_SMALL, fill=MUTED)
    if secret:
        d.text((W - 30, 90), secret, font=F_SMALL, fill=RED, anchor="ra")
    draw_matrix(d, list(cols), n, w, row, col, new)
    if scale:
        draw_scale(d, list(cols), *scale)
    if reading is not None:
        shown = list(reading) + ["?"] * (w - len(reading))
        txt = "(" + ", ".join(fmt(r) if r != "?" else "?" for r in shown) + ")"
        d.text((MX, 340), "scale readings:", font=F_SMALL, fill=MUTED)
        d.text((MX, 362), txt, font=font(28, True), fill=BLUE)
    d.multiline_text((40, H - 100), status, font=F, fill=status_color, spacing=6)
    return img


# ---------- the GIF ----------

def make_gif(n, w, heavies, name):
    frames, durations = [], []
    add = lambda img, ms: (frames.append(img), durations.append(ms))
    title = f"Heavy coin, oblivious: n = {n} coins, w = {w} weighings"
    sub = f"3^{w - 1} = {3 ** (w - 1)} < {n} < 3^{w} = {3 ** w}: too many coins for w = {w - 1}, " \
          f"too few to use every signature"
    F_ = lambda **kw: frame(n, w, title, sub, **kw)

    add(F_(status=f"Each coin needs a distinct column (its signature), and every row must sum to 0\n"
                  f"so the genuine weight g cancels out of every weighing."), 3000)

    # naive: first n signatures in order
    naive = list(itertools.product((-1, 0, 1), repeat=w))[:n]
    j = next(j for j in range(w) if sum(c[j] for c in naive))
    add(F_(cols=naive, status="First try: just take the first n signatures in order.\n"
                              "Columns are distinct, but the row sums aren't 0.", status_color=RED), 3000)
    left = [i for i, c in enumerate(naive) if c[j] == 1]
    right = [i for i, c in enumerate(naive) if c[j] == -1]
    small, big = (left, right) if len(left) < len(right) else (right, left)
    h = small[0] if small else next(i for i, c in enumerate(naive) if c[j] == 0)
    side = lambda s: "left" if s is left else "right"
    add(F_(cols=naive, row=j, scale=(j, h, True),
           status=f"Weighing {j + 1}: {len(left)} coin(s) left vs {len(right)} right. Even with heavy coin "
                  f"{LETTERS[h]} on the {side(small)} pan,\nthe {side(big)} pan wins every time. "
                  f"The reading tells you nothing.", status_color=RED), 4500)

    # build by cancelling pairs
    good = pair_columns(n, w)
    for k in range(0, n - n % 2, 2):
        a, b = LETTERS[k], LETTERS[k + 1]
        add(F_(cols=good[:k + 1], new=(k,),
               status=f"Add coin {a} = {vec(good[k])}. Row sums are now off by exactly that vector.",
               status_color=AMBER), 1600)
        add(F_(cols=good[:k + 2], new=(k + 1,),
               status=f"Add its partner {b} = {vec(good[k + 1])} = -{a}. Every entry cancels: "
                      f"row sums back to 0.", status_color=GREEN), 2000)
    if n % 2:
        add(F_(cols=good, new=(n - 1,),
               status=f"n is odd, so one coin is left over. Give {LETTERS[n - 1]} the zero column: it sits out\n"
                      f"every weighing, so it adds 0 to every row (and nothing else can be its partner).",
               status_color=GREEN), 3500)
    add(F_(cols=good, status=f"{n} distinct columns, every row sums to 0.\n"
                             f"These {w} weighings are now fixed in advance: that's what oblivious means.",
           status_color=GREEN), 3000)

    # run the fixed weighings
    for h in heavies:
        secret = f"secretly heavy: {LETTERS[h]} (the algorithm doesn't know)"
        reading = []
        add(F_(cols=good, reading=reading, secret=secret,
               status="Run the same weighings, in order, no matter what happens."), 1500)
        for j in range(w):
            reading.append(weigh(good, j, h)[3])
            add(F_(cols=good, row=j, scale=(j, h), reading=reading, secret=secret,
                   status=f"Weighing {j + 1} is row {j + 1}: put the +1 coins left, the -1 coins right."), 2200)
        why = "every weighing balanced, so it's the coin that never touched the scale" if not any(reading) \
            else "row sums are 0, so only the heavy coin can tip the scale"
        add(F_(cols=good, col=h, scale=(w - 1, h, True), reading=reading, secret=secret,
               status=f"Readings {vec(reading)} = column {LETTERS[h]} → {LETTERS[h]} is heavy.\n({why})",
               status_color=GREEN), 4000)

    path = os.path.join(HERE, name)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"wrote {path} ({len(frames)} frames)")


if __name__ == "__main__":
    make_gif(7, 2, heavies=[3, 6], name="coin_pairs_n7.gif")
    make_gif(6, 2, heavies=[1, 4], name="coin_pairs_n6.gif")
