"""
fib_ladder.gif: why repeated squaring leaks n and the Montgomery ladder doesn't.
Two inputs, n = 13 (1101) and n = 8 (1000), run side by side.

Act 1, square-and-multiply: every bit squares, 1-bits also multiply by Q.
    The observer's trace (one grey block per matrix product, no values) has
    long rounds for 1-bits and short rounds for 0-bits, so it spells out n.
Act 2, ladder: hold (Q^k, Q^(k+1)), compute all three products
    Q^(2k), Q^(2k+1), Q^(2k+2) every round, keep two of them.
    The answers differ, but both traces are 3 blocks per round: identical.

Requires Pillow.
"""

import os

from PIL import Image, ImageDraw

from fib_matrix_animation import (AMBER, AMBER_SOFT, BG, BLUE, BLUE_SOFT, F, F_BIG, F_SMALL, F_TITLE, FG, FIB,
                                  GREEN, GREEN_SOFT, H, MUTED, RED, RED_SOFT, RULE, W)

HERE = os.path.dirname(os.path.abspath(__file__))
B = 4
INPUTS = (13, 8)
PANEL_X = (40, 540)
BLOCK = "#8a94a3"


def bits(n):
    return [int(c) for c in format(n, f"0{B}b")]


def chip(d, x, y, text, soft="#ffffff", strong=RULE, w=92, strike=False, faded=False):
    d.rounded_rectangle([x, y, x + w, y + 36], radius=6, fill=soft, outline=strong,
                        width=2 if strong != RULE else 1)
    d.text((x + w / 2, y + 18), text, font=F, fill=MUTED if faded else FG, anchor="mm")
    if strike:
        d.line([x + 6, y + 30, x + w - 6, y + 6], fill=RED, width=2)


def draw_bits(d, x0, n, cur):
    d.text((x0, 108), f"n = {n:2d} =", font=F, fill=FG)
    for i, b in enumerate(bits(n)):
        x = x0 + 100 + i * 40
        on = i == cur
        d.rounded_rectangle([x, 98, x + 34, 132], radius=5, fill=BLUE_SOFT if on else "#ffffff",
                            outline=BLUE if on else RULE, width=2 if on else 1)
        d.text((x + 17, 115), str(b), font=F_BIG, fill=FG, anchor="mm")


def draw_trace(d, x0, rounds, y=392):
    """rounds: list of block counts per round. Only shapes, no values: what a timing/power probe sees."""
    d.text((x0, y - 28), "what an observer sees (one block = one product):", font=F_SMALL, fill=MUTED)
    x = x0
    for r, k in enumerate(rounds):
        for _ in range(k):
            d.rectangle([x, y, x + 16, y + 44], fill=BLOCK)
            x += 20
        d.text((x - 10 * k - 2, y + 58), f"r{r + 1}", font=F_SMALL, fill=MUTED, anchor="mm")
        x += 18
    d.text((x0 + 420, y + 22), f"{sum(rounds)}", font=F_BIG, fill=FG, anchor="rm")


def base(title, sub):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((40, 28), title, font=F_TITLE, fill=FG)
    d.text((40, 62), sub, font=F, fill=MUTED)
    d.line([520, 96, 520, 470], fill=RULE, width=1)
    return im, d


# ---------------------------------------------------------------- act 1

def act1(frames):
    title = "Act 1: plain repeated squaring leaks n"
    sub = "Each round squares. 1-bits also multiply by Q. Watch the grey blocks."
    for rnd in range(B + 1):                     # rnd = rounds finished
        im, d = base(title, sub)
        for x0, n in zip(PANEL_X, INPUTS):
            bs = bits(n)
            draw_bits(d, x0, n, rnd if rnd < B else None)
            k, rounds = 0, []
            for b in bs[:rnd]:
                k = 2 * k + b
                rounds.append(1 + b)
            d.text((x0, 170), "holding", font=F, fill=MUTED)
            chip(d, x0 + 90, 160, f"Q^{k}", BLUE_SOFT, BLUE)
            if rnd < B:
                b = bs[rnd]
                d.text((x0, 232), f"bit {b}:", font=F, fill=FG)
                chip(d, x0 + 90, 222, "square", w=100)
                if b:
                    chip(d, x0 + 200, 222, "x Q", AMBER_SOFT, AMBER, w=70)
                    d.text((x0, 288), f"Q^{k} -> Q^{2 * k} -> Q^{2 * k + 1}", font=F, fill=FG)
                else:
                    d.text((x0, 288), f"Q^{k} -> Q^{2 * k}", font=F, fill=FG)
            else:
                d.text((x0, 232), f"done: F({n}) = top-right of Q^{n} = {FIB[n]}", font=F, fill=GREEN)
            draw_trace(d, x0, rounds)
        if rnd == B:
            d.text((40, 492), "Long round (2 blocks) = bit 1, short round (1 block) = bit 0.", font=F, fill=RED)
            d.text((40, 518), "The observer reads 1101 on the left and 1000 on the right without seeing a",
                   font=F, fill=RED)
            d.text((40, 540), "single value. In RSA, n is the private key.", font=F, fill=RED)
        frames.append((im, 2200 if rnd < B else 6000))


# ---------------------------------------------------------------- act 2

def act2(frames):
    title = "Act 2: the ladder does the same work for every bit"
    sub = "Hold Q^k and Q^(k+1). Compute all 3 products every round, then keep 2 of them."
    for rnd in range(B + 1):
        for phase in (("compute", "keep") if rnd < B else ("done",)):
            im, d = base(title, sub)
            for x0, n in zip(PANEL_X, INPUTS):
                bs = bits(n)
                draw_bits(d, x0, n, rnd if rnd < B else None)
                k = 0
                for b in bs[:rnd]:
                    k = 2 * k + b
                rounds = [3] * rnd + ([3] if phase == "keep" else [])
                d.text((x0, 170), "holding", font=F, fill=MUTED)
                chip(d, x0 + 90, 160, f"Q^{k}", BLUE_SOFT, BLUE)
                chip(d, x0 + 192, 160, f"Q^{k + 1}", BLUE_SOFT, BLUE)
                if phase == "done":
                    d.text((x0, 232), f"done: F({n}) = top-right of Q^{n} = {FIB[n]}", font=F, fill=GREEN)
                    draw_trace(d, x0, rounds)
                    continue
                b = bs[rnd]
                exps = (2 * k, 2 * k + 1, 2 * k + 2)
                keep = (exps[1], exps[2]) if b else (exps[0], exps[1])
                d.text((x0, 232), "compute", font=F, fill=MUTED)
                for j, e in enumerate(exps):
                    x = x0 + 90 + j * 102
                    if phase == "compute":
                        chip(d, x, 222, f"Q^{e}", AMBER_SOFT, AMBER)
                    elif e in keep:
                        chip(d, x, 222, f"Q^{e}", GREEN_SOFT, GREEN)
                    else:
                        chip(d, x, 222, f"Q^{e}", RED_SOFT, RED, strike=True, faded=True)
                if phase == "compute":
                    d.text((x0, 288), "always all three, whatever the bit", font=F, fill=AMBER)
                else:
                    which = "the right two" if b else "the left two"
                    d.text((x0, 288), f"bit {b}: keep {which} -> (Q^{keep[0]}, Q^{keep[1]})", font=F, fill=GREEN)
                    d.text((x0, 312), "picked by arithmetic, no if-statement", font=F_SMALL, fill=MUTED)
                draw_trace(d, x0, rounds)
            if phase == "done":
                d.text((40, 492), "Different inputs, different answers, but the two traces are identical:",
                       font=F, fill=GREEN)
                d.text((40, 518), "3 blocks every round. The observer can't tell 13 from 8.", font=F, fill=GREEN)
                d.text((40, 540), "The cost: one product per round is computed and thrown away.", font=F, fill=MUTED)
            frames.append((im, 2400 if phase != "done" else 7000))


if __name__ == "__main__":
    frames = []
    act1(frames)
    act2(frames)
    ims, durs = zip(*frames)
    path = os.path.join(HERE, "fib_ladder.gif")
    ims[0].save(path, save_all=True, append_images=list(ims[1:]), duration=list(durs), loop=0)
    print("wrote", path, len(ims), "frames")
