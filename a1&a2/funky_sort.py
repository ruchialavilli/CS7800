import random

comparisons = 0
swaps = 0


def funky_sort(A, trace=False):
    """Sort A in place. Pseudocode is 1-indexed; Python is 0-indexed."""
    global comparisons, swaps
    n = len(A)
    for i in range(n):
        for j in range(n):
            comparisons += 1
            if A[i] < A[j]:
                A[i], A[j] = A[j], A[i]
                swaps += 1
        if trace:
            print(f"after i={i}: {A}   prefix A[0..{i}] = {A[:i + 1]}")


def test(trials=2000, max_n=30):
    for _ in range(trials):
        n = random.randint(0, max_n)
        A = [random.randint(0, 10) for _ in range(n)]
        B = A[:]
        funky_sort(B)
        assert B == sorted(A), f"FAILED on {A} -> {B}"
    print(f"all {trials} random tests passed")


def measure(ns=(4, 8, 16, 32, 64, 128)):
    global comparisons, swaps
    print(f"{'n':>5} {'comparisons':>12} {'swaps(rev)':>11} {'swaps(sorted)':>14}")
    for n in ns:
        comparisons = swaps = 0
        funky_sort(list(range(n, 0, -1)))
        rev_swaps, comps = swaps, comparisons
        swaps = 0
        funky_sort(list(range(1, n + 1)))
        print(f"{n:>5} {comps:>12} {rev_swaps:>11} {swaps:>14}")


if __name__ == "__main__":
    test()
    measure()
    print("\n--- trace ---")
    funky_sort([5, 2, 8, 1, 9, 3], trace=True)
