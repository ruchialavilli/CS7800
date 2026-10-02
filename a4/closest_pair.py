"""
Closest pair of points: O(n log^2 n) vs O(n log n).

Both versions sort by x once, split at the median x, recurse on each half, and
then check the strip of points within delta of the median line, where delta is
the best distance found in either half. They differ only in how the strip gets
sorted by y.

closest_pair_resort  re-sorts the strip by y in every call:
    T(n) = 2T(n/2) + O(n log n)   ->   O(n log^2 n)
    (level i has 2^i calls of size n/2^i, costing n log(n/2^i) in total, and
     the sum over levels i = 0..log n of n(log n - i) is Theta(n log^2 n))

closest_pair         has every call return its points sorted by y, so the
                     parent only merges two sorted lists, as in mergesort:
    T(n) = 2T(n/2) + O(n)         ->   O(n log n)

Claim: closest_pair_rec(pts, lo, hi), where pts is sorted by x, returns
(the closest pair in pts[lo:hi], pts[lo:hi] sorted by y), in O(n log n) time
for n = hi - lo.

Proof of correctness, by strong induction on n.
  Base (n <= 3): brute force is exact, and sorting at most 3 points is O(1).
  Step: the two recursive calls return the correct best pairs for their halves
  and both halves sorted by y (inductive hypothesis). Let delta be the smaller
  of the two best distances. Any pair closer than delta either lies in one half,
  which is already covered, or straddles the line x = median. Then both points
  are within delta of the line, so both are in the strip, and their
  y-difference is less than delta. Merging two y-sorted lists gives a y-sorted
  list, and filtering keeps that order, so the strip is sorted by y. Scanning
  each strip point against the points after it until the y-gap reaches delta
  therefore finds every straddling pair closer than delta. The function returns
  the merged list, which is all of pts[lo:hi] sorted by y.

Packing bound (why the strip scan is linear): for a strip point p, every point
it is compared with lies in the rectangle 2*delta wide (across the line) by
delta tall (above p). Divide that rectangle into 8 squares of side delta/2.
Each square lies entirely on one side of the line, and its diagonal is
delta/sqrt(2) < delta, so it holds at most one point, since two points on the
same side are at least delta apart. (Points exactly on the line can be split
into either half by index; the boundary case still allows only O(1) points per
square.) So each point is compared with at most 7 others, and the scan is O(n).

Running time: one presort by x costs O(n log n). Each call with n points does
O(n) merging, O(n) filtering and O(7n) scanning, plus two calls of size n/2:
    T(n) = 2T(n/2) + cn,  T(3) = O(1)
The recursion has log n levels, each doing cn work in total, so
T(n) = O(n log n) by case 2 of the Master Theorem. The total is
O(n log n) + O(n log n) = O(n log n).

This is optimal for comparison-based algorithms: element distinctness reduces
to closest pair (put x_i at (x_i, 0) and ask whether the minimum distance is
0), and element distinctness needs Omega(n log n) comparisons.
"""

import math
import random
from functools import cmp_to_key

Y_COMPARISONS = [0]       # y-order comparisons made while sorting or merging


def cmp_y(p, q):
    Y_COMPARISONS[0] += 1
    return (p[1] > q[1]) - (p[1] < q[1])


BY_Y = cmp_to_key(cmp_y)


def brute_force(points):
    # check each point against each other, O(n^2)
    best = (float('inf'), None)
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = math.dist(points[i], points[j])
            if d < best[0]:
                best = (d, (points[i], points[j]))
    return best


def scan_strip(strip, best):
    # strip is sorted by y; compare each point only with those less than delta above it
    delta = best[0]
    for i in range(len(strip)):
        j = i + 1
        while j < len(strip) and strip[j][1] - strip[i][1] < delta:
            d = math.dist(strip[i], strip[j])
            if d < delta:
                best, delta = (d, (strip[i], strip[j])), d
            j += 1
    return best


# ---------- O(n log^2 n): re-sort the strip by y at every level ----------

def resort_rec(pts, lo, hi):
    if hi - lo <= 3:
        return brute_force(pts[lo:hi])
    mid = (lo + hi) // 2
    median = pts[mid][0]
    best = min(resort_rec(pts, lo, mid), resort_rec(pts, mid, hi), key=lambda b: b[0])
    strip = sorted((p for p in pts[lo:hi] if abs(p[0] - median) < best[0]),
                   key=BY_Y)                             # O(n log n) per call
    return scan_strip(strip, best)


def closest_pair_resort(graph):
    if len(graph) < 2:
        raise ValueError("insufficient data: need at least 2 points")
    pts = sorted(graph, key=lambda p: p[0])
    return resort_rec(pts, 0, len(pts))


# ---------- O(n log n): return y-sorted lists and merge them ----------

def merge_by_y(left, right):
    # merge step of mergesort: two y-sorted lists -> one y-sorted list, O(n)
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if cmp_y(left[i], right[j]) <= 0:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def closest_pair_rec(pts, lo, hi):
    # returns ((distance, pair), pts[lo:hi] sorted by y)
    if hi - lo <= 3:
        base = pts[lo:hi]
        return brute_force(base), sorted(base, key=BY_Y)   # O(1): at most 3 points
    mid = (lo + hi) // 2
    median = pts[mid][0]
    best_left, left_y = closest_pair_rec(pts, lo, mid)
    best_right, right_y = closest_pair_rec(pts, mid, hi)
    best = min(best_left, best_right, key=lambda b: b[0])
    merged = merge_by_y(left_y, right_y)                             # O(n) per call
    strip = [p for p in merged if abs(p[0] - median) < best[0]]      # stays sorted by y
    return scan_strip(strip, best), merged


def closest_pair(graph):
    if len(graph) < 2:
        raise ValueError("insufficient data: need at least 2 points")
    pts = sorted(graph, key=lambda p: p[0])
    best, _ = closest_pair_rec(pts, 0, len(pts))
    return best


def test():
    for _ in range(500):
        n = random.randint(2, 50)
        pts = [(random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(n)]
        expected = brute_force(pts)[0]
        for f in (closest_pair_resort, closest_pair):
            assert math.isclose(f(pts)[0], expected), (f.__name__, pts)
    # small integer grid, so duplicate points and ties show up often
    for _ in range(500):
        n = random.randint(2, 20)
        pts = [(random.randint(0, 5), random.randint(0, 5)) for _ in range(n)]
        expected = brute_force(pts)[0]
        for f in (closest_pair_resort, closest_pair):
            assert math.isclose(f(pts)[0], expected), (f.__name__, pts)
    print("all random tests passed")


def count_comparisons():
    # Worst case for the strip: x values are tiny, so every point is in the strip
    # at every level. y is shuffled so the re-sort can't take Timsort's O(n) path
    # for already-sorted input. Wall-clock time is a poor check in Python, where C
    # sorting beats interpreted loops, so count y-comparisons instead. Divided by
    # n lg n, closest_pair should stay flat while closest_pair_resort grows
    # like lg n.
    print(f"{'n':>8} {'resort / n lg n':>16} {'merge / n lg n':>16}")
    rng = random.Random(0)
    for n in [2 ** e for e in range(10, 18)]:
        ys = list(range(n))
        rng.shuffle(ys)
        pts = [(1e-9 * i, y) for i, y in enumerate(ys)]
        row = []
        for f in (closest_pair_resort, closest_pair):
            Y_COMPARISONS[0] = 0
            f(pts)
            row.append(Y_COMPARISONS[0] / (n * math.log2(n)))
        print(f"{n:>8} {row[0]:>16.2f} {row[1]:>16.2f}")


if __name__ == "__main__":
    test()
    count_comparisons()
