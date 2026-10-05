"""
Animations of hashing for element distinctness in the word-RAM model.

hash_lookup.gif     each key goes through h(x) = ((a*x + b) mod p) mod m to an
                    address in the table T[0..m-1]. Only keys that land in the
                    same slot are compared, and only for equality.

hash_bad_vs_universal.gif
                    the same keys (multiples of 8) under two hash functions.
                    Left: fixed h(x) = x mod 8, so every key lands in T[0] and
                    the k-th key is compared with all k-1 before it: n(n-1)/2
                    comparisons, the brute-force cost. Right: a and b drawn at
                    random from the universal family above, where any two
                    distinct keys collide with probability about 1/m, so the
                    expected number of comparisons is C(n,2)/m.

Requires Pillow.
"""

import os
import random

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 960, 540
BG, FG, MUTED, RULE = "#f7f8fa", "#1b2330", "#6b7685", "#c9d1dc"
BLUE, BLUE_SOFT = "#2f5bd3", "#dbe4fa"
GREEN, GREEN_SOFT = "#2e8b57", "#d6efe0"
AMBER, AMBER_SOFT = "#b7791f", "#fbedd0"
RED, RED_SOFT = "#c23d2a", "#f8dcd7"


def font(size, bold=False):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size, index=1 if bold else 0)
    except OSError:
        return ImageFont.load_default(size=size)


F_TITLE, F_BIG, F, F_SMALL = font(22, True), font(20), font(16), font(13)


def box(d, x, y, w, h, text, fill, outline, fnt=F, color=FG, width=2):
    d.rounded_rectangle([x, y, x + w, y + h], radius=5, fill=fill, outline=outline, width=width)
    d.text((x + w / 2, y + h / 2), str(text), font=fnt, fill=color, anchor="mm")


def arrow(d, x0, y0, x1, y1, color, width=3):
    d.line([x0, y0, x1, y1], fill=color, width=width)
    d.polygon([(x1, y1), (x1 - 7, y1 - 12), (x1 + 7, y1 - 12)], fill=color)


def save(frames, durations, name):
    path = os.path.join(HERE, name)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"wrote {path} ({len(frames)} frames)")


# ---------- GIF 1: step-by-step lookup ----------

def hash_lookup_gif():
    keys = [42, 17, 93, 8, 61, 30, 75, 93]
    a, b, p, m = 2, 17, 101, 8
    h = lambda x: ((a * x + b) % p) % m

    table = [[] for _ in range(m)]
    frames, durations = [], []
    hashed = compares = 0
    KX, KW = 60, 90
    SX, SW, SY = 60, 96, 300

    def draw(cur, stage, slot=None, cmp_idx=None, status="", status_color=FG, dup=False):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.text((40, 24), "Hashing in the word-RAM: one address computation per key", font=F_TITLE, fill=FG)
        d.text((40, 58), f"h(x) = (({a}·x + {b}) mod {p}) mod {m}     a, b were drawn at random once",
               font=F_SMALL, fill=MUTED)
        # input
        d.text((40, 92), "input", font=F_SMALL, fill=MUTED)
        for i, x in enumerate(keys):
            if i == cur:
                fill, out = (RED_SOFT, RED) if dup else (BLUE_SOFT, BLUE)
            elif cur is not None and i < cur:
                fill, out = "#eceff3", RULE
            else:
                fill, out = "#ffffff", RULE
            done = cur is not None and i < cur
            box(d, KX + i * (KW + 10), 110, KW, 40, x, fill, out, color=MUTED if done else FG)
        # formula
        if cur is not None and stage >= 1:
            x = keys[cur]
            d.text((40, 186), f"h({x}) = (({a}·{x} + {b}) mod {p}) mod {m} = ({(a * x + b) % p}) mod {m} = {h(x)}",
                   font=F_BIG, fill=BLUE)
            d.text((40, 218), f"→ go straight to address T[{h(x)}]: one memory access, no searching",
                   font=F_SMALL, fill=MUTED)
        # table
        d.text((40, SY - 34), "memory: T[0..7]", font=F_SMALL, fill=MUTED)
        for s in range(m):
            sx = SX + s * (SW + 12)
            active = slot == s and stage >= 2
            d.rounded_rectangle([sx, SY, sx + SW, SY + 34], radius=5,
                                fill=BLUE_SOFT if active else "#ffffff", outline=BLUE if active else RULE, width=2)
            d.text((sx + SW / 2, SY + 17), f"T[{s}]", font=F, fill=BLUE if active else MUTED, anchor="mm")
            for k, v in enumerate(table[s]):
                fill, out = "#ffffff", FG
                if active and cmp_idx == k:
                    fill, out = (RED_SOFT, RED) if dup else (AMBER_SOFT, AMBER)
                box(d, sx + 8, SY + 46 + k * 40, SW - 16, 32, v, fill, out)
        if cur is not None and stage >= 2:
            sx = SX + slot * (SW + 12) + SW / 2
            arrow(d, sx, 236, sx, SY - 6, BLUE)
        # status and counters
        d.text((40, 470), status, font=F, fill=status_color)
        d.text((W - 40, 500), f"keys hashed: {hashed}    equality checks: {compares}",
               font=F, fill=FG, anchor="ra")
        return img

    def add(img, ms):
        frames.append(img)
        durations.append(ms)

    add(draw(None, 0, status="Goal: is any key repeated?"), 1400)
    for i, x in enumerate(keys):
        s = h(x)
        add(draw(i, 0, status=f"next key: {x}"), 600)
        hashed += 1
        add(draw(i, 1, status=f"compute h({x}) with ordinary arithmetic"), 1100)
        if not table[s]:
            add(draw(i, 2, s, status=f"T[{s}] is empty → store {x}. Zero comparisons.", status_color=GREEN), 1000)
            table[s].append(x)
            add(draw(i, 2, s, status=f"T[{s}] is empty → store {x}. Zero comparisons.", status_color=GREEN), 700)
            continue
        found = False
        for k, v in enumerate(table[s]):
            compares += 1
            if v == x:
                found = True
                add(draw(i, 2, s, k, f"T[{s}] holds {v}. Is {x} = {v}? YES → DUPLICATE FOUND", RED, dup=True), 3500)
                break
            add(draw(i, 2, s, k, f"T[{s}] holds {v}. Is {x} = {v}? no (a collision, not a duplicate)",
                     AMBER), 1500)
        if found:
            break
        table[s].append(x)
        add(draw(i, 2, s, status=f"append {x} to the chain in T[{s}]", status_color=GREEN), 900)
    save(frames, durations, "hash_lookup.gif")


# ---------- GIF 2: adversarial keys, fixed vs random hash ----------

def bad_vs_universal_gif(seed=7):
    keys = [8 * i for i in range(12)]
    p, m = 101, 8
    rng = random.Random(seed)
    a, b = rng.randrange(1, p), rng.randrange(0, p)
    hashes = [("h(x) = x mod 8", "fixed: an adversary can pick keys that collide", lambda x: x % m),
              (f"h(x) = (({a}x + {b}) mod {p}) mod 8", "a, b random: Pr[h(x) = h(y)] ≈ 1/8",
               lambda x: ((a * x + b) % p) % m)]
    tables = [[[] for _ in range(m)] for _ in hashes]
    counts = [0, 0]
    frames, durations = [], []
    SW, SY, HALF = 50, 170, W // 2

    def draw(cur, slots=None):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.text((40, 20), "Same keys, two hash functions", font=F_TITLE, fill=FG)
        keytxt = "keys: " + " ".join(
            (f"[{x}]" if i == cur else str(x)) for i, x in enumerate(keys))
        d.text((40, 54), keytxt, font=F_SMALL, fill=FG)
        d.line([HALF, 90, HALF, H - 20], fill=RULE, width=2)
        for side, (name, sub, _) in enumerate(hashes):
            ox = side * HALF + 30
            d.text((ox, 92), name, font=F, fill=RED if side == 0 else GREEN)
            d.text((ox, 116), sub, font=F_SMALL, fill=MUTED)
            for s in range(m):
                sx = ox + s * (SW + 3)
                hit = slots is not None and slots[side] == s
                d.rounded_rectangle([sx, SY - 30, sx + SW, SY - 4], radius=4,
                                    fill=BLUE_SOFT if hit else "#ffffff", outline=BLUE if hit else RULE, width=2)
                d.text((sx + SW / 2, SY - 17), f"T{s}", font=F_SMALL, fill=BLUE if hit else MUTED, anchor="mm")
                for k, v in enumerate(tables[side][s]):
                    new = hit and k == len(tables[side][s]) - 1
                    box(d, sx + 3, SY + k * 25, SW - 6, 22, v, BLUE_SOFT if new else "#ffffff",
                        BLUE if new else RULE, fnt=F_SMALL, width=1)
            n = sum(len(t) for t in tables[side])
            d.text((ox, H - 52), f"equality checks: {counts[side]}", font=F_BIG,
                   fill=RED if side == 0 else GREEN)
            worst = n * (n - 1) // 2
            d.text((ox, H - 26), f"after {n} keys   (brute force would be {worst})", font=F_SMALL, fill=MUTED)
        return img

    frames.append(draw(None))
    durations.append(1500)
    for i, x in enumerate(keys):
        slots = []
        for side, (_, _, h) in enumerate(hashes):
            s = h(x)
            counts[side] += len(tables[side][s])     # compared with everything already there
            tables[side][s].append(x)
            slots.append(s)
        frames.append(draw(i, slots))
        durations.append(900)
    frames.append(draw(None))
    durations.append(4000)
    print(f"random hash a={a}, b={b}: {counts[1]} checks vs {counts[0]} for x mod 8")
    save(frames, durations, "hash_bad_vs_universal.gif")


if __name__ == "__main__":
    hash_lookup_gif()
    bad_vs_universal_gif()
