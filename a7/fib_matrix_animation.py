"""
Three animations for the linear-algebra half of oblivious_fibonacci.py, meant
to be watched in order:

fib_step.gif          One Fibonacci step is a matrix-vector product:
                      [F(k+1), F(k)] = Q x [F(k), F(k-1)],  Q = [1 1; 1 0].
                      Top row of Q adds the last two numbers, bottom row
                      copies the old top number down.
fib_matrix_power.gif  Doing the step n times is multiplying by Q n times, so
                      the work collapses into one matrix Q^n -- and Q^n itself
                      is made of Fibonacci numbers: [F(n+1) F(n); F(n) F(n-1)].
fib_squaring.gif      Repeated squaring: Q^a x Q^a = Q^(2a) doubles the
                      exponent, so Q^13 takes 5 multiplications instead of 12.
                      The extra "x Q" happens only on 1-bits of n, which is the
                      leak the Montgomery ladder removes.

Requires Pillow.
"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1040, 580
BG, FG, MUTED, RULE = "#f7f8fa", "#1b2330", "#6b7685", "#c9d1dc"
BLUE, BLUE_SOFT = "#2f5bd3", "#dbe4fa"
GREEN, GREEN_SOFT = "#2e8b57", "#d6efe0"
AMBER, AMBER_SOFT = "#b7791f", "#fbedd0"
RED, RED_SOFT = "#c23d2a", "#f8dcd7"
CW, CH, GAP = 76, 48, 6               # matrix cell size and spacing

FIB = [0, 1]
while len(FIB) < 20:
    FIB.append(FIB[-1] + FIB[-2])


def font(size, bold=False):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size, index=1 if bold else 0)
    except OSError:
        return ImageFont.load_default(size=size)


F_TITLE, F_BIG, F, F_SMALL = font(22, True), font(26, True), font(16), font(13)


def mat_mul(X, Y):
    return [[sum(X[i][t] * Y[t][j] for t in range(len(Y))) for j in range(len(Y[0]))] for i in range(len(X))]


def mat_pow(k):
    R = [[1, 0], [0, 1]]
    for _ in range(k):
        R = mat_mul(R, [[1, 1], [1, 0]])
    return R


def frame(title, sub=""):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((40, 28), title, font=F_TITLE, fill=FG)
    if sub:
        d.text((40, 62), sub, font=F, fill=MUTED)
    return im, d


def mat_width(M):
    return len(M[0]) * CW + (len(M[0]) - 1) * GAP + 20


def draw_matrix(d, x, cy, M, fills=None, row_hl=None, label=None):
    """Draw M with its vertical center at cy. fills maps (i, j) -> (soft, strong). Returns the width."""
    rows, cols = len(M), len(M[0])
    h = rows * CH + (rows - 1) * GAP
    top = cy - h / 2
    for i in range(rows):
        for j in range(cols):
            cx, y = x + 10 + j * (CW + GAP), top + i * (CH + GAP)
            soft, strong = (fills or {}).get((i, j), ("#ffffff", RULE))
            hl = row_hl is not None and i == row_hl
            d.rounded_rectangle([cx, y, cx + CW, y + CH], radius=6, fill=soft,
                                outline=RED if hl else strong, width=3 if hl or strong != RULE else 1)
            v = M[i][j]
            d.text((cx + CW / 2, y + CH / 2), str(v), font=F_BIG if len(str(v)) < 4 else F,
                   fill=MUTED if v == "?" else FG, anchor="mm")
    w = mat_width(M)
    for bx, s in ((x, 1), (x + w, -1)):          # brackets
        d.line([bx, top - 6, bx, top + h + 6], fill=FG, width=2)
        d.line([bx, top - 6, bx + 8 * s, top - 6], fill=FG, width=2)
        d.line([bx, top + h + 6, bx + 8 * s, top + h + 6], fill=FG, width=2)
    if label:
        d.text((x + w / 2, top + h + 26), label, font=F_SMALL, fill=MUTED, anchor="mm")
    return w


def equation(d, cy, parts, x=60):
    """parts: matrices (dicts with M/fills/label/row_hl) and strings, laid out left to right."""
    for p in parts:
        if isinstance(p, str):
            d.text((x + 22, cy), p, font=F_BIG, fill=FG, anchor="mm")
            x += 44
        else:
            x += draw_matrix(d, x, cy, p["M"], p.get("fills"), p.get("row_hl"), p.get("label")) + 4


def fib_strip(d, colors, y=490, upto=14):
    """F(0)..F(upto-1) as a row of boxes; colors maps index -> (soft, strong)."""
    bw, x0 = 64, 40
    d.text((x0, y - 26), "the Fibonacci sequence", font=F_SMALL, fill=MUTED)
    for i in range(upto):
        x = x0 + i * (bw + 4)
        soft, strong = colors.get(i, ("#ffffff", RULE))
        d.rounded_rectangle([x, y, x + bw, y + 40], radius=5, fill=soft, outline=strong,
                            width=2 if strong != RULE else 1)
        d.text((x + bw / 2, y + 20), str(FIB[i]), font=F, fill=FG, anchor="mm")
        d.text((x + bw / 2, y + 54), f"F({i})", font=F_SMALL, fill=MUTED, anchor="mm")


def save(frames, name):
    ims, durs = zip(*frames)
    path = os.path.join(HERE, name)
    ims[0].save(path, save_all=True, append_images=list(ims[1:]), duration=list(durs), loop=0)
    print("wrote", path)


GREENS, AMBERS, BLUES = (GREEN_SOFT, GREEN), (AMBER_SOFT, AMBER), (BLUE_SOFT, BLUE)


# ---------------------------------------------------------------- 1. one step

def step_gif():
    frames = []
    title = "One Fibonacci step is a matrix times a vector"
    sub = "Keep the last two numbers in a vector. Multiplying by Q gives the next pair."
    Q = [[1, 1], [1, 0]]

    for k in range(1, 8):
        a, b = FIB[k], FIB[k - 1]                     # old vector [F(k), F(k-1)]
        new = [[FIB[k + 1]], [FIB[k]]]
        old = {"M": [[a], [b]], "fills": {(0, 0): GREENS, (1, 0): AMBERS},
               "label": f"[F({k}), F({k - 1})]"}
        q = {"M": Q, "label": "Q"}
        detailed = k <= 3

        def draw(result, fills, row_hl, lines, strip, dur):
            im, d = frame(title, sub)
            equation(d, 230, [{"M": result, "fills": fills, "label": f"[F({k + 1}), F({k})]"}, "=",
                              dict(q, row_hl=row_hl), "x", dict(old, row_hl=row_hl)], x=120)
            for i, (txt, col) in enumerate(lines):
                d.text((120, 345 + i * 30), txt, font=F, fill=col)
            fib_strip(d, strip)
            frames.append((im, dur))

        top = (f"top row:     1·{a} + 1·{b} = {a + b}   new number = sum of the last two", FG)
        bot = (f"bottom row:  1·{a} + 0·{b} = {a}   the old top number slides down", FG)
        old_strip = {k: GREENS, k - 1: AMBERS}
        if detailed:
            draw([["?"], ["?"]], {}, 0, [top], old_strip, 1800)
            draw([[new[0][0]], ["?"]], {(0, 0): BLUES}, 1, [top, bot], {**old_strip, k + 1: BLUES}, 1800)
        draw(new, {(0, 0): BLUES, (1, 0): GREENS}, None,
             [top, bot] if detailed else [(f"[{a + b}, {a}] = Q x [{a}, {b}]", FG)],
             {k + 1: BLUES, k: GREENS}, 1600 if detailed else 900)

    im, d = frame(title, sub)
    d.text((120, 200), "Every step multiplies by the same matrix Q.", font=F_TITLE, fill=FG)
    d.text((120, 250), "So after n steps, starting from [F(1), F(0)] = [1, 0]:", font=F, fill=FG)
    d.text((120, 300), "[F(n+1), F(n)]  =  Q x Q x ... x Q  x [1, 0]  =  Q^n x [1, 0]", font=F_BIG, fill=BLUE)
    d.text((120, 360), "Next: what does Q^n look like? (fib_matrix_power.gif)", font=F, fill=MUTED)
    frames.append((im, 3500))
    save(frames, "fib_step.gif")


# ---------------------------------------------------------------- 2. Q^n

def power_gif():
    frames = []
    title = "Q^n is made of Fibonacci numbers"
    sub = "Multiply by Q one more time and the entries shift one place along the sequence."
    Q = [[1, 1], [1, 0]]
    colors = lambda: {(0, 0): GREENS, (0, 1): BLUES, (1, 0): BLUES, (1, 1): AMBERS}

    for k in range(1, 9):
        im, d = frame(title, sub)
        P = mat_pow(k)
        if k == 1:
            equation(d, 220, [{"M": P, "fills": colors(), "label": "Q^1"}, "=", {"M": Q, "label": "Q"}], x=120)
        else:
            equation(d, 220, [{"M": P, "fills": colors(), "label": f"Q^{k}"}, "=",
                              {"M": mat_pow(k - 1), "label": f"Q^{k - 1}"}, "x", {"M": Q, "label": "Q"}], x=120)
        d.text((120, 330), f"green = F({k + 1})    blue = F({k})    amber = F({k - 1})", font=F, fill=FG)
        d.text((120, 362), f"F({k}) = {FIB[k]} is the top-right entry of Q^{k}", font=F, fill=BLUE)
        fib_strip(d, {k + 1: GREENS, k: BLUES, k - 1: AMBERS})
        frames.append((im, 1500 if k < 8 else 2500))

    im, d = frame(title, sub)
    equation(d, 220, [{"M": [["F(n+1)", "F(n)"], ["F(n)", "F(n-1)"]], "fills": colors(), "label": "Q^n"}], x=120)
    d.text((330, 190), "To get F(n), compute the matrix Q^n and", font=F, fill=FG)
    d.text((330, 216), "read off its top-right entry.", font=F, fill=FG)
    d.text((330, 262), "Doing it one Q at a time takes n - 1 products.", font=F, fill=MUTED)
    d.text((330, 288), "Next: squaring gets there much faster (fib_squaring.gif)", font=F, fill=MUTED)
    frames.append((im, 3500))
    save(frames, "fib_matrix_power.gif")


# ---------------------------------------------------------------- 3. repeated squaring

def squaring_gif(n=13):
    frames = []
    title = f"Repeated squaring: Q^{n} in a handful of products"
    sub = "Q^a x Q^a = Q^(2a) doubles the exponent. Read n's bits left to right."
    bits = bin(n)[2:]
    Q = [[1, 1], [1, 0]]

    # plan: list of (exponent, how we got there, bit index)
    plan, e = [(1, "start", 0)], 1
    for i, bit in enumerate(bits[1:], 1):
        e *= 2
        plan.append((e, "square", i))
        if bit == "1":
            e += 1
            plan.append((e, "x Q", i))

    def draw(step, dur, final=False):
        im, d = frame(title, sub)
        # bits of n
        d.text((40, 108), f"n = {n} = binary", font=F, fill=FG)
        cur_bit = plan[step][2]
        for i, b in enumerate(bits):
            x = 232 + i * 40
            on = i == cur_bit and not final
            d.rounded_rectangle([x, 98, x + 34, 132], radius=5, fill=BLUE_SOFT if on else "#ffffff",
                                outline=BLUE if on else RULE, width=2 if on else 1)
            d.text((x + 17, 115), b, font=F_BIG, fill=FG, anchor="mm")
        d.text((250 + len(bits) * 40, 108), "0 bit: square    1 bit: square, then x Q",
               font=F_SMALL, fill=MUTED)

        # exponent timeline
        x = 40
        for s, (ex, how, _) in enumerate(plan):
            done, cur = s < step, s == step
            soft, strong = (BLUE_SOFT, BLUE) if cur else ((GREEN_SOFT, GREEN) if done or final else ("#ffffff", RULE))
            if s:
                d.text((x + 30, 172), "square" if how == "square" else "x Q", font=F_SMALL,
                       fill=AMBER if how == "x Q" else MUTED, anchor="mm")
                d.line([x + 6, 190, x + 54, 190], fill=RULE, width=2)
                d.polygon([(x + 54, 185), (x + 62, 190), (x + 54, 195)], fill=RULE)
                x += 66
            d.rounded_rectangle([x, 172, x + 76, 208], radius=6, fill=soft, outline=strong,
                                width=2 if strong != RULE else 1)
            d.text((x + 38, 190), f"Q^{ex}", font=F, fill=FG if s <= step or final else MUTED, anchor="mm")
            x += 76

        # current equation
        ex, how, _ = plan[step]
        hi = {(0, 1): BLUES} if final else {}
        if how == "start":
            equation(d, 320, [{"M": Q, "label": "Q^1", "fills": hi}], x=60)
            d.text((300, 310), "start from Q (the leading 1 bit)", font=F, fill=FG)
        elif how == "square":
            prev = ex // 2
            equation(d, 320, [{"M": mat_pow(ex), "label": f"Q^{ex}", "fills": hi}, "=",
                              {"M": mat_pow(prev), "label": f"Q^{prev}"}, "x",
                              {"M": mat_pow(prev), "label": f"Q^{prev}"}], x=60)
        else:
            equation(d, 320, [{"M": mat_pow(ex), "label": f"Q^{ex}", "fills": hi}, "=",
                              {"M": mat_pow(ex - 1), "label": f"Q^{ex - 1}"}, "x", {"M": Q, "label": "Q"}], x=60)

        used = step
        d.text((40, 420), f"matrix products so far: {used}", font=F_TITLE, fill=BLUE)
        d.text((40, 452), f"one Q at a time would take {n - 1}", font=F, fill=MUTED)
        if final:
            d.text((520, 420), f"F({n}) = top-right of Q^{n} = {FIB[n]}", font=F_TITLE, fill=GREEN)
            d.text((40, 500), "For n = 1,000,000 (20 bits): one Q at a time = 999,999 products; squaring = at most 38.",
                   font=F, fill=FG)
            d.text((40, 530), "Notice the 'x Q' only happens on 1-bits, so watching the work reveals n.",
                   font=F, fill=AMBER)
            d.text((40, 552), "That is the leak the ladder in oblivious_fibonacci.py removes.", font=F, fill=AMBER)
        frames.append((im, dur))

    for s in range(len(plan)):
        draw(s, 2000)
    draw(len(plan) - 1, 6000, final=True)
    save(frames, "fib_squaring.gif")


if __name__ == "__main__":
    step_gif()
    power_gif()
    squaring_gif()
