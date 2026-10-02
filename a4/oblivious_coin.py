"""
Odd coin problem, oblivious (non-adaptive) version: n coins, exactly one is
counterfeit and it is either heavier OR lighter. Find it and whether it is
heavy or light with a balance scale -- but every weighing must be decided
BEFORE seeing any result. The a3 solution was adaptive (each weighing depended
on prior outcomes); here the whole schedule is fixed up front, run as one
batch, and the batch of outcomes is decoded at the end.

Encoding: give coin i a codeword c_i in {-1, 0, +1}^k, one digit per weighing
    +1 -> coin goes on the left pan in that weighing
    -1 -> coin goes on the right pan
     0 -> coin sits out
If coin i is heavy, the outcome vector is exactly c_i; if light, it is -c_i.
So decoding works iff
    1. no codeword is all zeros               (else that coin is invisible)
    2. the 2n vectors {c_i} and {-c_i} are distinct (else two answers collide)
    3. every weighing has as many +1s as -1s  (equal coins per pan; no
                                               known-genuine coin to pad with)

Bound: the adaptive lower bound n <= (3^k - 3) / 2 applies here too, and
Dyson showed it is achievable obliviously, so going non-adaptive costs nothing.
For k = 3 that is still 12 coins.

Construction (Dyson): call a non-constant vector "clockwise" if, at the first
position where consecutive digits differ, the digit steps forward on the cycle
-1 -> 0 -> +1 -> -1. Exactly one of v, -v is clockwise (negation reverses the
cycle), and adding 1 to every digit (cyclically) keeps clockwise vectors
clockwise. That shift splits the (3^k - 3) / 2 clockwise vectors into triples
{v, v+1, v+2}, and each triple has one -1, one 0 and one +1 in every
position, so any set of whole triples gives balanced weighings. For
n = 3m + r with r > 0 we take m + 1 triples and apply a small fix-up (see
fixup()) that removes 3 - r codewords while keeping every weighing balanced.
For n = 4, 5 there are too few triples for the fix-up, so a short search over
the unused pairs {v, -v} finds the last few codewords instead.
"""

from functools import lru_cache
from itertools import product

NEXT = {-1: 0, 0: 1, 1: -1}


class Scale:
    """A balance scale that only accepts a full batch of weighings at once."""

    def __init__(self, weights):
        self.weights = weights
        self.uses = 0

    def weigh(self, left, right):
        """Return 1 if left is heavier, -1 if right is heavier, 0 if balanced."""
        self.uses += 1
        l = sum(self.weights[i] for i in left)
        r = sum(self.weights[i] for i in right)
        return (l > r) - (l < r)

    def weigh_batch(self, schedule):
        """Run every (left, right) weighing in order and return all outcomes together."""
        return tuple(self.weigh(left, right) for left, right in schedule)


def clockwise(v):
    for a, b in zip(v, v[1:]):
        if a != b:
            return b == NEXT[a]
    return False                                   # constant vector


def shift(v):
    return tuple(NEXT[x] for x in v)


def neg(v):
    return tuple(-x for x in v)


def triples(k):
    """All shift-triples {v, v+1, v+2} of clockwise vectors of length k."""
    seen, out = set(), []
    for v in product((-1, 0, 1), repeat=k):
        if clockwise(v) and v not in seen:
            t = (v, shift(v), shift(shift(v)))
            seen.update(t)
            out.append(t)
    return out


def solve_tail(size, used, k):
    """Pick `size` vectors from unused pairs {v, -v} so every position sums to 0."""
    reps = [v for v in product((-1, 0, 1), repeat=k)
            if any(v) and v not in used and neg(v) not in used and v > neg(v)]

    def dfs(start, chosen, sums):
        left = size - len(chosen)
        if left == 0:
            return chosen if not any(sums) else None
        if any(abs(s) > left for s in sums):       # each vector moves a sum by at most 1
            return None
        for j in range(start, len(reps)):
            for v in (reps[j], neg(reps[j])):
                found = dfs(j + 1, chosen + [v], [s + x for s, x in zip(sums, v)])
                if found:
                    return found
        return None

    return dfs(0, [], [0] * k)


def fixup(r, k):
    """
    (remove, negate, add) turning a balanced set of whole triples into one with
    3 - r fewer codewords that is still balanced (all listed vectors are clockwise).
    Removing u shifts each position's sum by -u, negating u by -2u, adding u by +u.
        r = 2: remove (-1,-1,0..), (0,0,1..1); negate (1,-1,0..), (0,1,-1,0..),
               (0,1,1,0..); add the constant (1..1), whose pair no triple uses
        r = 1: remove (1,-1,0..), (-1,-1,0..); negate (0,1,0..)
    """
    def v(*head):
        return tuple(head) + (0,) * (k - len(head))
    if r == 2:
        return [v(-1, -1), (0, 0) + (1,) * (k - 2)], [v(1, -1), v(0, 1, -1), v(0, 1, 1)], [(1,) * k]
    return [v(1, -1), v(-1, -1)], [v(0, 1)], []


@lru_cache(maxsize=None)
def codewords(n):
    """Codeword for each coin 0..n-1, satisfying conditions 1-3 above."""
    k = min_weighings(n)
    m, r = divmod(n, 3)
    if r == 0:
        return tuple(v for t in triples(k)[:m] for v in t)
    # take m + 1 whole triples and apply the fix-up that drops 3 - r of them
    remove, negate, add = fixup(r, k)
    touched = set(remove + negate)
    T = sorted(triples(k), key=lambda t: not touched & set(t))   # touched triples first
    if all(t in T[:m + 1] for t in triples(k) if touched & set(t)):
        words = [v for t in T[:m + 1] for v in t if v not in remove]
        return tuple([neg(v) if v in negate else v for v in words] + add)
    # too few triples to hold the fix-up (n = 4, 5): search for a balanced tail,
    # giving whole triples back to the search until one exists
    for drop in range(1, m + 1):
        words = [v for t in triples(k)[:m - drop] for v in t]
        tail = solve_tail(3 * drop + r, set(words), k)
        if tail:
            return tuple(words + tail)
    raise ValueError(f"no balanced codewords for n={n}")


def schedule(n):
    """The fixed list of weighings, in order: [(left coins, right coins), ...]."""
    words = codewords(n)
    return [([i for i, w in enumerate(words) if w[j] == 1],
             [i for i, w in enumerate(words) if w[j] == -1])
            for j in range(min_weighings(n))]


def decode(n, outcomes):
    """Map a batch of outcomes to (index, +1 if heavy / -1 if light)."""
    for i, w in enumerate(codewords(n)):
        if w == outcomes:
            return i, 1
        if neg(w) == outcomes:
            return i, -1
    raise ValueError(f"outcomes {outcomes} match no coin")


def find_odd(scale, n):
    """Commit to the whole schedule, weigh it as one batch, then decode."""
    return decode(n, scale.weigh_batch(schedule(n)))


def min_weighings(n):
    """Smallest k with (3^k - 3) / 2 >= n. Needs n >= 3 (with 1 or 2 coins, heavy vs light can't be told)."""
    if n < 3:
        raise ValueError("need at least 3 coins to tell heavy from light")
    k = 1
    while (3 ** k - 3) // 2 < n:
        k += 1
    return k


def test(max_n=120):
    for n in range(3, max_n + 1):
        k = min_weighings(n)
        plan = schedule(n)
        assert len(plan) == k, f"n={n}: {len(plan)} weighings, bound {k}"
        for left, right in plan:
            assert len(left) == len(right), f"n={n}: unbalanced pans"
        # the same precomputed schedule is reused for every possible odd coin
        for odd in range(n):
            for sign in (1, -1):
                weights = [10] * n
                weights[odd] += sign
                scale = Scale(weights)
                assert find_odd(scale, n) == (odd, sign), f"wrong: n={n}, odd={odd}, sign={sign}"
                assert scale.uses == k
    print(f"All tests passed for n = 3..{max_n}")


def show(n):
    k = min_weighings(n)
    print(f"\nn={n}: {k} weighings, fixed in advance")
    for j, (left, right) in enumerate(schedule(n), 1):
        print(f"  weighing {j}: {left} vs {right}")
    sym = {1: "L", -1: "R", 0: "-"}
    print("  coin codewords (L = left pan, R = right pan, - = off):")
    for i, w in enumerate(codewords(n)):
        print(f"    coin {i:>2}: {''.join(sym[x] for x in w)}")


if __name__ == "__main__":
    test()
    show(12)
    for n in [12, 13, 39, 40]:
        print(f"n={n:>3}: {min_weighings(n)} weighings")
