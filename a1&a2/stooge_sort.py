import random

calls = 0
max_depth = 0


def stooge_sort(A, lo, hi, depth=1):
    """Sort A[lo..hi] (inclusive) in place."""
    global calls, max_depth
    calls += 1
    max_depth = max(max_depth, depth)

    n = hi - lo + 1
    if n <= 1:
        return
    if n == 2:
        if A[lo] > A[hi]:
            A[lo], A[hi] = A[hi], A[lo]
        return

    t = n // 3
    stooge_sort(A, lo, hi - t, depth + 1)  # first 2/3
    stooge_sort(A, lo + t, hi, depth + 1)  # last 2/3
    stooge_sort(A, lo, hi - t, depth + 1)  # first 2/3 again


def test(trials=2000, max_n=30):
    for _ in range(trials):
        n = random.randint(0, max_n)
        A = [random.randint(0, 10) for _ in range(n)]
        B = A[:]
        stooge_sort(B, 0, len(B) - 1)
        assert B == sorted(A), f"FAILED on {A} -> {B}"
    print(f"all {trials} random tests passed")


def measure(ns=(3, 6, 9, 27, 81, 243)):
    global calls, max_depth
    print(f"{'n':>5} {'calls':>10} {'max_depth':>10}")
    for n in ns:
        calls = max_depth = 0
        A = list(range(n, 0, -1))
        stooge_sort(A, 0, n - 1)
        print(f"{n:>5} {calls:>10} {max_depth:>10}")


if __name__ == "__main__":
    test()
    measure()
