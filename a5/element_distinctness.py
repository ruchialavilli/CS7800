"""
Element distinctness: given x_1..x_n, are they all different?

Three algorithms:

distinct_brute   compare every pair                    O(n^2) comparisons
distinct_sort    mergesort, then check neighbours      O(n log n) comparisons
distinct_hash    bucket by floor(x), compare within    O(n) expected, but it
                 a bucket only                         uses floor(), which is
                                                       not a comparison

Geometric decision trees. Treat the whole input as ONE point
x = (x_1, ..., x_n) in R^n. A comparison "x_i vs x_j" is the sign of the
linear function x_i - x_j, so it asks which side of the hyperplane x_i = x_j
the point is on (<, = or >). Any comparison algorithm, run on every possible
input, is a ternary tree: internal nodes are hyperplane tests and each leaf is
the answer for every input that took that path. Tracer below records the path
as a list of (i, j, sign) triples, which is exactly the list of half-spaces
the input satisfied.

Claim: any comparison algorithm needs ceil(log_3(n!)) = Theta(n log n)
comparisons in the worst case.

Proof.
  1. The set of inputs reaching a leaf is an intersection of half-spaces
     {x : x_i - x_j < 0} or {> 0} or hyperplanes {= 0}, one per test on the
     path. Intersections of half-spaces are convex.
  2. The all-distinct inputs are R^n minus the hyperplanes x_i = x_j. Two
     inputs with the same ordering x_p(1) < ... < x_p(n) lie in a convex set,
     so in one piece. Two inputs with different orderings disagree on some
     pair i, j, and any path between them crosses x_i = x_j (intermediate
     value theorem on x_i - x_j). So there are exactly n! pieces.
  3. A leaf answering "distinct" cannot hold inputs a, b from two pieces: its
     region is convex, so the segment from a to b is inside it, and that
     segment crosses some x_i = x_j at a duplicate input. The leaf would give
     the wrong answer there.
  4. So there are at least n! leaves. A ternary tree of depth d has at most
     3^d leaves, so d >= log_3(n!), and by Stirling's approximation
     log n! = n log n - n log e + O(log n) = Theta(n log n).

distinct_hash escapes the bound because floor(x) cuts R^n with infinitely
many parallel hyperplanes x_i = k at once, and its leaves are not convex
(write_regions_svg draws this for n = 3).

Reduction to closest pair: put x_i at (x_i, 0). The closest pair is at
distance 0 iff two x_i are equal, so closest pair also needs Omega(n log n),
and the O(n log n) divide and conquer in a4/closest_pair.py is optimal.
"""

import math
import os
import random


class Tracer:
    # records every comparison as the hyperplane test it is: sign(x_i - x_j)
    def __init__(self, xs):
        self.xs = xs
        self.tests = []

    def cmp(self, i, j):
        d = self.xs[i] - self.xs[j]
        s = (d > 0) - (d < 0)
        self.tests.append((i, j, s))
        return s

    def path(self):
        sym = {-1: "<", 0: "=", 1: ">"}
        return [f"x{i + 1} - x{j + 1} {sym[s]} 0" for i, j, s in self.tests]


def distinct_brute(xs, tr=None):
    tr = tr or Tracer(xs)
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            if tr.cmp(i, j) == 0:
                return False
    return True


def merge_sort(idx, tr):
    # sorts indices by value; returns None as soon as a comparison says "="
    if len(idx) <= 1:
        return idx
    mid = len(idx) // 2
    left = merge_sort(idx[:mid], tr)
    right = left is not None and merge_sort(idx[mid:], tr)
    if not right:
        return None
    merged = []
    a = b = 0
    while a < len(left) and b < len(right):
        s = tr.cmp(left[a], right[b])
        if s == 0:
            return None
        if s < 0:
            merged.append(left[a])
            a += 1
        else:
            merged.append(right[b])
            b += 1
    merged.extend(left[a:])
    merged.extend(right[b:])
    return merged


def distinct_sort(xs, tr=None):
    tr = tr or Tracer(xs)
    order = merge_sort(list(range(len(xs))), tr)
    if order is None:
        return False
    # equal values would now be neighbours
    return all(tr.cmp(order[k], order[k + 1]) != 0 for k in range(len(order) - 1))


def distinct_hash(xs, tr=None):
    # floor(x) picks the bucket; only values sharing a bucket are compared.
    # tr.buckets records the bucket-collision pattern, the non-comparison part
    # of the path.
    tr = tr or Tracer(xs)
    buckets = {}
    tr.buckets = []
    for i, x in enumerate(xs):
        b = buckets.setdefault(math.floor(x), [])
        tr.buckets.append(len(b) > 0)
        for j in b:
            if tr.cmp(i, j) == 0:
                return False
        b.append(i)
    return True


# ---------- tests and comparison counts ----------

def test():
    for _ in range(2000):
        n = random.randint(0, 30)
        xs = [random.randint(0, 3 * n) for _ in range(n)]     # duplicates are common
        if random.random() < 0.5:
            xs = [x + random.random() for x in xs]
        expected = len(set(xs)) == len(xs)
        for f in (distinct_brute, distinct_sort, distinct_hash):
            assert f(xs) == expected, (f.__name__, xs)
    print("all random tests passed")


def count_comparisons():
    # Distinct inputs are the hard case: no early "=" exit. log2(n!) is the
    # information-theoretic minimum for a binary tree; Stirling's estimate
    # n log2 n - n log2 e + log2(2 pi n) / 2 tracks it closely.
    print(f"{'n':>6} {'brute':>10} {'sort':>9} {'ceil lg n!':>11} {'Stirling':>9} "
          f"{'n lg n':>9} {'sort / lg n!':>13}")
    rng = random.Random(0)
    for n in [2 ** e for e in range(2, 14)]:
        xs = rng.sample(range(10 * n), n)
        lg_fact = math.lgamma(n + 1) / math.log(2)
        stirling = n * math.log2(n) - n * math.log2(math.e) + math.log2(2 * math.pi * n) / 2
        counts = []
        for f in (distinct_brute, distinct_sort):
            tr = Tracer(xs)
            f(xs, tr)
            counts.append(len(tr.tests))
        print(f"{n:>6} {counts[0]:>10} {counts[1]:>9} {math.ceil(lg_fact):>11} "
              f"{stirling:>9.1f} {n * math.log2(n):>9.1f} {counts[1] / lg_fact:>13.2f}")


def show_path(xs):
    tr = Tracer(xs)
    ans = distinct_sort(xs, tr)
    print(f"\ninput {xs} is the point {tuple(xs)} in R^{len(xs)}")
    print("hyperplane tests on its root-to-leaf path:")
    for t in tr.path():
        print("   ", t)
    print("leaf:", "ALL DISTINCT" if ans else "DUPLICATE")


# ---------- picture of the leaves for n = 3 ----------

# Project R^3 along (1,1,1): e1, e2, e3 map to unit vectors 120 degrees apart.
# Moving along (1,1,1) changes no comparison, so nothing is lost.
U = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in (90, 210, 330)]
PALETTE = ["#4e79a7", "#f28e2b", "#59a14f", "#b07aa1", "#edc948", "#76b7b2",
           "#ff9da7", "#9c755f", "#bab0ac", "#86bcb6", "#d4a6c8", "#a0cbe8"]


def to_values(px, py):
    return [5 + (px * u[0] + py * u[1]) / 40 for u in U]


def leaf_of(f, xs):
    tr = Tracer(xs)
    f(xs, tr)
    return (tuple(getattr(tr, "buckets", ())), tuple(tr.tests))


def panel(f, ox, title, subtitle, size=300, step=2, label_wedges=False):
    c, r = size / 2, size / 2 - 20
    out = [f'<text x="{ox + c}" y="22" class="t">{title}</text>',
           f'<text x="{ox + c}" y="40" class="s">{subtitle}</text>']
    colors, counts = {}, {}
    top = 50
    rows = []
    for sy in range(0, size, step):
        run_start, run_leaf = None, None
        for sx in range(0, size + step, step):
            px, py = sx - c + step / 2, c - sy - step / 2    # half-step offset: never exactly on x_i = x_j
            inside = sx < size and px * px + py * py <= r * r
            leaf = leaf_of(f, to_values(px, py)) if inside else None
            if leaf != run_leaf:
                if run_leaf is not None:
                    col = colors.setdefault(run_leaf, PALETTE[len(colors) % len(PALETTE)])
                    rows.append(f'<rect x="{ox + run_start}" y="{top + sy}" width="{sx - run_start}" '
                                f'height="{step}" fill="{col}"/>')
                run_start, run_leaf = sx, leaf
            if leaf is not None:
                counts[leaf] = counts.get(leaf, 0) + 1
    out += rows
    # duplicate hyperplanes x_i = x_j, which are lines through the centre
    for a in (30, 90, 150):
        dx, dy = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        out.append(f'<line x1="{ox + c + dx}" y1="{top + c - dy}" x2="{ox + c - dx}" y2="{top + c + dy}" '
                   f'stroke="#c0392b" stroke-width="2"/>')
    out.append(f'<circle cx="{ox + c}" cy="{top + c}" r="{r}" fill="none" stroke="#333"/>')
    if label_wedges:
        for a in range(0, 360, 60):
            px, py = 92 * math.cos(math.radians(a)), 92 * math.sin(math.radians(a))
            xs = to_values(px, py)
            order = "&lt;".join(f"x{i + 1}" for i in sorted(range(3), key=lambda i: xs[i]))
            out.append(f'<text x="{ox + c + px}" y="{top + c - py + 4}" class="w">{order}</text>')
    return out, len(colors), counts


def write_regions_svg(path):
    a, n_a, _ = panel(distinct_sort, 0, "distinct_sort (comparisons)",
                      "every leaf is one convex wedge", label_wedges=True)
    b, n_b, counts = panel(distinct_hash, 330, "distinct_hash (floor buckets)",
                           "leaves are not convex")
    # the hash leaf "no bucket collisions" answers with zero comparisons
    free = max(counts, key=lambda k: (not any(k[0]), counts[k]))
    share = counts[free] / sum(counts.values())
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 420" width="640" height="420" shape-rendering="crispEdges">',
           '<style>text{font-family:Menlo,monospace;text-anchor:middle;fill:#222}'
           '.t{font-size:14px;font-weight:bold}.s{font-size:11px;fill:#555}'
           '.w{font-size:11px;font-weight:bold;fill:#fff;paint-order:stroke;stroke:#0006;stroke-width:2px}</style>',
           '<rect width="640" height="420" fill="#fff"/>']
    svg += a + b
    svg.append(f'<text x="165" y="385" class="s">{n_a} leaves = 3! regions, one per ordering</text>')
    svg.append(f'<text x="495" y="385" class="s">{n_b} leaves; one leaf ("no collisions",</text>')
    svg.append(f'<text x="495" y="400" class="s">0 comparisons) covers {share:.0%} of the disk</text>')
    svg.append('<text x="320" y="414" class="s">looking down (1,1,1); red: x_i = x_j; same colour = same leaf</text>')
    svg.append('</svg>')
    with open(path, "w") as fh:
        fh.write("\n".join(svg))
    print(f"\nwrote {path}: distinct_sort has {n_a} leaves, distinct_hash has {n_b}")


if __name__ == "__main__":
    test()
    count_comparisons()
    show_path([4, 7, 2])
    show_path([4, 7, 4])
    write_regions_svg(os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaf_regions.svg"))
