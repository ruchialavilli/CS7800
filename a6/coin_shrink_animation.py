"""
The same construction as coin_pairs_animation.py, run top-down: start from the
full 3^w matrix (every signature once, every row sums to 0) and remove columns
until n are left.

In product order the full matrix is mirror-symmetric: column i and column
3^w - 1 - i are negatives, and the middle column is the zero column. Removing a
single column breaks the row sums; removing a mirror pair (or the zero column)
doesn't. 3^w - n columns have to go, and since 3^w is odd, that's an odd count
exactly when n is even, which is when the zero column goes.

coin_shrink_n7.gif   9 → 7: remove one pair.
coin_shrink_n6.gif   9 → 6: remove the zero column, then one pair.

Requires Pillow.
"""

import itertools
import os

from PIL import Image, ImageDraw

from coin_pairs_animation import (AMBER, AMBER_SOFT, BG, BLUE, BLUE_SOFT, F, F_BIG, F_SMALL, F_TITLE, FG, GREEN,
                                  H, LETTERS, MUTED, RED, RULE, W, fmt, pair_columns, vec)

HERE = os.path.dirname(os.path.abspath(__file__))
MX, MY, CW, CH = 40, 150, 46, 40


def draw_matrix(d, cols, w, gone=(), hl=(), arcs=False, labels=None):
    N = len(cols)
    xs = [MX + 90 + i * (CW + 4) for i in range(N)]
    bottom = MY + w * (CH + 6) - 6
    for i, c in enumerate(cols):
        d.text((xs[i] + CW / 2, MY - 18), (labels or LETTERS)[i], font=F,
               fill=MUTED if i in gone else FG, anchor="mm")
    for j in range(w):
        y = MY + j * (CH + 6)
        d.text((MX, y + CH / 2), f"weigh {j + 1}", font=F_SMALL, fill=MUTED, anchor="lm")
        for i, c in enumerate(cols):
            x, v = xs[i], c[j]
            if i in gone:
                d.rounded_rectangle([x, y, x + CW, y + CH], radius=5, fill="#eceff3", outline=RULE, width=1)
                d.text((x + CW / 2, y + CH / 2), fmt(v), font=F, fill=RULE, anchor="mm")
                continue
            fill = {1: BLUE_SOFT, -1: AMBER_SOFT, 0: "#ffffff"}[v]
            d.rounded_rectangle([x, y, x + CW, y + CH], radius=5, fill=fill,
                                outline=AMBER if i in hl else RULE, width=3 if i in hl else 1)
            d.text((x + CW / 2, y + CH / 2), fmt(v), font=F, fill=FG if v else MUTED, anchor="mm")
        live = [c for i, c in enumerate(cols) if i not in gone]
        s = sum(c[j] for c in live)
        d.text((MX + 100 + N * (CW + 4), y + CH / 2), f"sum = {s}", font=F,
               fill=GREEN if s == 0 else RED, anchor="lm")
        # per-row pan counts
        L = sum(c[j] == 1 for c in live)
        R = sum(c[j] == -1 for c in live)
        d.text((760, y + CH / 2), f"left {L}  right {R}  out {len(live) - L - R}", font=F_SMALL,
               fill=GREEN if L == R else RED, anchor="lm")
    for i in gone:                    # strike out removed columns
        d.line([xs[i] + 4, MY - 4, xs[i] + CW - 4, bottom], fill=RED, width=2)
    if arcs:
        for i in range(N // 2):
            k = N - 1 - i
            h = 14 + 12 * (N // 2 - 1 - i)
            color = RULE if i in gone else AMBER if i in hl else MUTED
            d.arc([xs[i] + CW / 2, bottom + 4 - h, xs[k] + CW / 2, bottom + 4 + h], 0, 180, fill=color, width=2)


def frame(title, sub, cols, w, status="", status_color=FG, **kw):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((40, 22), title, font=F_TITLE, fill=FG)
    d.text((40, 56), sub, font=F_SMALL, fill=MUTED)
    draw_matrix(d, cols, w, **kw)
    d.multiline_text((40, H - 120), status, font=F, fill=status_color, spacing=6)
    return img


def make_gif(n, w, name):
    frames, durations = [], []
    add = lambda img, ms: (frames.append(img), durations.append(ms))
    full = list(itertools.product((-1, 0, 1), repeat=w))
    N = len(full)
    idx = {c: i for i, c in enumerate(full)}
    mirror = lambda i: N - 1 - i
    title = f"Shrinking the full system: {N} signatures → {n} coins"
    sub = f"w = {w}. Remove {N} - {n} = {N - n} columns without breaking any row sum."
    F_ = lambda status, color=FG, **kw: frame(title, sub, full, w, status, color, **kw)

    add(F_(f"Start from all 3^{w} = {N} signatures. Every row has {N // 3} of each of +1, -1, 0,\n"
           f"so every row sums to 0. We already know this system works."), 3500)
    add(F_(f"In this order the matrix is a mirror: column i and column {N - 1}-i are negatives.\n"
           f"The middle column is all zeros, its own partner.", arcs=True), 4000)

    # what goes wrong removing one column on its own
    add(F_(f"Remove just one column, say {LETTERS[0]} = {vec(full[0])}:\n"
           f"every row it touched is now unbalanced.", RED, gone={0}, arcs=True), 3500)
    add(F_(f"So columns have to leave together with their partner:\n"
           f"{LETTERS[0]} with {LETTERS[mirror(0)]}, which gives back exactly what {LETTERS[0]} took.",
           hl={0, mirror(0)}, arcs=True), 3000)

    # actual removals: zero column if 9 - n is odd, then pairs (heaviest first)
    keep = set(map(idx.get, pair_columns(n, w)))
    gone = set()
    zero = idx[(0,) * w]
    if zero not in keep:
        add(F_(f"{N} - {n} = {N - n} is odd, so pairs alone can't do it. The zero column is the only\n"
               f"column that cancels by itself: remove {LETTERS[zero]}.", AMBER, gone=set(gone), hl={zero},
               arcs=True), 3000)
        gone.add(zero)
        add(F_(f"Removing {LETTERS[zero]} changes no row sum: it was never on the scale.", GREEN,
               gone=set(gone), arcs=True), 2500)
    drop = sorted((i for i in range(N // 2) if i not in keep), key=lambda i: -sum(map(abs, full[i])))
    for i in drop:
        p = {i, mirror(i)}
        add(F_(f"Remove the pair {LETTERS[i]} = {vec(full[i])} and {LETTERS[mirror(i)]} = "
               f"{vec(full[mirror(i)])}.", AMBER, gone=set(gone), hl=p, arcs=True), 2200)
        gone |= p
        add(F_(f"They cancel each other, so the row sums don't move.", GREEN, gone=set(gone), arcs=True), 2200)

    # compact survivors and relabel them as the actual coins
    survivors = [full[i] for i in range(N) if i not in gone]
    add(frame(title, sub, survivors, w,
              f"{n} distinct columns, every row sums to 0, and these are the coins A-{LETTERS[n - 1]}.\n"
              f"Same columns as coin_pairs_n{n}.gif (built up from pairs), just reordered: two directions,\n"
              f"one rule. Columns enter or leave only as cancelling groups.", GREEN), 5000)

    path = os.path.join(HERE, name)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"wrote {path} ({len(frames)} frames)")


if __name__ == "__main__":
    make_gif(7, 2, "coin_shrink_n7.gif")
    make_gif(6, 2, "coin_shrink_n6.gif")
