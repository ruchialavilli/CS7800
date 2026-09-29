# sandbox for assignments for CS7800
import math
import random
import time


def brute_force(points):
    # check each point against each other, O(n^2)
    # returns (distance, pair); distance is infinity if there are fewer than 2 points
    best = (float('inf'), None)
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = math.dist(points[i], points[j])
            if d < best[0]:
                best = (d, (points[i], points[j]))
    return best


def closest_pair_simple(graph: list[tuple[float, float]]):
    # earlier version: one split, brute force on each half and on the strip, O(n^2)
    if len(graph) < 2:
        raise ValueError("insufficient data: need at least 2 points")

    xs = [p[0] for p in graph]
    ys = [p[1] for p in graph]
    axis = 0 if (max(xs) - min(xs)) >= (max(ys) - min(ys)) else 1
    pts = sorted(graph, key=lambda p: p[axis])
    mid = len(pts) // 2
    left, right = pts[:mid], pts[mid:]
    median = pts[mid][axis]

    best = min(brute_force(left), brute_force(right), key=lambda b: b[0])
    delta = best[0]

    strip = [p for p in pts if abs(p[axis] - median) < delta]
    best_strip = brute_force(strip)
    if best_strip[0] < delta:
        best = best_strip

    if best[0] == float('inf'):
        raise ValueError("no pair found")
    return best


def merge_by_y(left, right):
    # merge step of mergesort: two y-sorted lists -> one y-sorted list, O(n)
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i][1] <= right[j][1]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def closest_pair_rec(pts, lo, hi):
    # pts is the master list sorted by x; this call works on pts[lo:hi] without copying it
    # returns ((distance, pair), pts[lo:hi] sorted by y)

    # base case: 2 or 3 points, brute force and return the points sorted by y
    if hi - lo <= 3:
        base = pts[lo:hi]
        return brute_force(base), sorted(base, key=lambda p: p[1])

    # divide by median along x axis (saved before recursing, the halves come back sorted by y)
    mid = (lo + hi) // 2
    median = pts[mid][0]

    # recurse on each half
    best_left, left_y = closest_pair_rec(pts, lo, mid)
    best_right, right_y = closest_pair_rec(pts, mid, hi)

    # combine: smallest pair of the two halves, then merge the y-lists
    best = min(best_left, best_right, key=lambda b: b[0])
    delta = best[0]
    merged = merge_by_y(left_y, right_y)

    # filter to the center strip (stays sorted by y because it comes from merged)
    strip = [p for p in merged if abs(p[0] - median) < delta]

    # nearest neighbor check: only points less than delta above in y, at most 7 per point
    for i in range(len(strip)):
        j = i + 1
        while j < len(strip) and strip[j][1] - strip[i][1] < delta:
            d = math.dist(strip[i], strip[j])
            if d < delta:
                best = (d, (strip[i], strip[j]))
                delta = d
            j += 1

    return best, merged


def closest_pair(graph: list[tuple[float, float]]):
    # check if data is sufficient, 2 or greater points
    if len(graph) < 2:
        raise ValueError("insufficient data: need at least 2 points")

    # sort by x once, here, so the recursive helper never has to re-sort
    pts = sorted(graph, key=lambda p: p[0])
    best, _ = closest_pair_rec(pts, 0, len(pts))
    return best


def main():
    # the earlier example: the closest pair straddles the median line
    print(closest_pair([(0, 0), (4.9, 0), (5.1, 0), (10, 0)]))

    # random tests against brute force
    for _ in range(500):
        n = random.randint(2, 50)
        pts = [(random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(n)]
        got, expected = closest_pair(pts)[0], brute_force(pts)[0]
        assert math.isclose(got, expected), (pts, got, expected)

    # small integer grid, so duplicate points and ties show up often
    for _ in range(500):
        n = random.randint(2, 20)
        pts = [(random.randint(0, 5), random.randint(0, 5)) for _ in range(n)]
        got, expected = closest_pair(pts)[0], brute_force(pts)[0]
        assert math.isclose(got, expected), (pts, got, expected)

    print("all random tests passed")

    # worst case for the strip: every point lands in it
    n = 3000
    pts = [(0.0001 * i, i) for i in range(n)]
    for f in (closest_pair_simple, closest_pair):
        start = time.perf_counter()
        result = f(pts)
        print(f"{f.__name__:20} {time.perf_counter() - start:.4f}s  {result[0]:.4f}")


if __name__ == "__main__":
    main()
