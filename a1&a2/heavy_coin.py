"""
Odd coin problem: n coins, exactly one is counterfeit and it is either heavier
OR lighter (we don't know which). Find the coin and whether it is heavy or light
using a balance scale. Classic case: 12 coins in 3 weighings.

Bookkeeping: every coin is in one of four states
    U - unknown         (never on the scale during an unbalanced weighing,
                         never cleared): could be heavy or light
    H - maybe heavy     (was on the heavy pan): can only be the heavy one
    L - maybe light     (was on the light pan): can only be the light one
    G - known genuine
The number of possible answers is 2|U| + |H| + |L|.

After weighing (left vs right, equal coin counts):
    balanced    -> every coin on the scale is genuine
    left heavy  -> odd coin is in (U∩left or H∩left) as heavy,
                   or (U∩right or L∩right) as light; everything else genuine
    right heavy -> mirror image

Since only the counts matter, plan() searches over how many coins of each state
go on each pan, so each remaining outcome can still be solved in the weighings left.

Lower bound: k weighings give 3^k outcome sequences and we need 2n answers, so
2n <= 3^k. It's actually tighter: with no known-genuine coin to start, the
all-balanced sequence can't tell you heavy vs light, and the first weighing
must be u vs u, which gives n <= (3^k - 3) / 2 (Dyson). For k = 3 that is 12.
"""

from functools import lru_cache


class Scale:
    """A balance scale that counts how many times it has been used."""

    def __init__(self, weights):
        self.weights = weights
        self.uses = 0

    def weigh(self, left, right):
        """Return 1 if left is heavier, -1 if right is heavier, 0 if balanced."""
        self.uses += 1
        l = sum(self.weights[i] for i in left)
        r = sum(self.weights[i] for i in right)
        return (l > r) - (l < r)


@lru_cache(maxsize=None)
def plan(u, h, l, g, k):
    """
    Given state counts and k weighings left, return a weighing
    (uL, uR, hL, hR, lL, lR, gL, gR) that guarantees success,
    () if the answer is already determined, or None if impossible.
    """
    if 2 * u + h + l <= 1:
        return ()
    if k == 0 or 2 * u + h + l > 3 ** k:
        return None
    cap = 3 ** (k - 1)                             # max answers per outcome
    for uL in range(u + 1):
        for uR in range(u - uL + 1):
            for hL in range(h + 1):
                for hR in range(h - hL + 1):
                    for lL in range(l + 1):
                        for lR in range(l - lL + 1):
                            on = uL + uR + hL + hR + lL + lR
                            if on == 0:
                                continue
                            diff = (uL + hL + lL) - (uR + hR + lR)
                            if abs(diff) > g:      # pad lighter side with genuine coins
                                continue
                            gL, gR = max(0, -diff), max(0, diff)
                            # (u, h, l, g) after each outcome
                            bal = (u - uL - uR, h - hL - hR, l - lL - lR, g + on)
                            lh = (0, uL + hL, uR + lR)
                            rh = (0, uR + hR, uL + lL)
                            n = u + h + l + g
                            lh += (n - lh[1] - lh[2],)
                            rh += (n - rh[1] - rh[2],)
                            if any(2 * s[0] + s[1] + s[2] > cap for s in (bal, lh, rh)):
                                continue
                            if all(plan(*s, k - 1) is not None for s in (bal, lh, rh)):
                                return (uL, uR, hL, hR, lL, lR, gL, gR)
    return None


def find_odd(scale, n):
    """Return (index, +1 if heavy / -1 if light) of the odd coin among 0..n-1."""
    U, H, L, G = list(range(n)), [], [], []
    k = min_weighings(n)
    while 2 * len(U) + len(H) + len(L) > 1:
        uL, uR, hL, hR, lL, lR, gL, gR = plan(len(U), len(H), len(L), len(G), k)
        left = U[:uL] + H[:hL] + L[:lL] + G[:gL]
        right = U[uL:uL + uR] + H[hL:hL + hR] + L[lL:lL + lR] + G[gL:gL + gR]
        result = scale.weigh(left, right)
        k -= 1
        if result == 0:
            on_scale = set(left) | set(right)
            U = [i for i in U if i not in on_scale]
            H = [i for i in H if i not in on_scale]
            L = [i for i in L if i not in on_scale]
        elif result > 0:
            U, H, L = [], U[:uL] + H[:hL], U[uL:uL + uR] + L[lL:lL + lR]
        else:
            U, H, L = [], U[uL:uL + uR] + H[hL:hL + hR], U[:uL] + L[:lL]
        suspects = set(U) | set(H) | set(L)
        G = [i for i in range(n) if i not in suspects]
    return (H[0], 1) if H else (L[0], -1)


def min_weighings(n):
    """Smallest k with (3^k - 3) / 2 >= n. Needs n >= 3 (with 1 or 2 coins, heavy vs light can't be told)."""
    if n < 3:
        raise ValueError("need at least 3 coins to tell heavy from light")
    k = 1
    while (3 ** k - 3) // 2 < n:
        k += 1
    return k


def test(max_n=39):
    for n in range(3, max_n + 1):
        k = min_weighings(n)
        worst = 0
        for odd in range(n):
            for sign in (1, -1):
                weights = [10] * n
                weights[odd] += sign
                scale = Scale(weights)
                assert find_odd(scale, n) == (odd, sign), f"wrong: n={n}, odd={odd}, sign={sign}"
                worst = max(worst, scale.uses)
        assert worst == k, f"n={n}: used {worst}, bound {k}"
        # the solver itself confirms k - 1 weighings are not enough
        assert plan(n, 0, 0, 0, k - 1) is None, f"n={n}: solvable in {k - 1}?"
    print(f"All tests passed for n = 3..{max_n}")


if __name__ == "__main__":
    test()
    for n in [12, 13, 39, 40]:
        print(f"n={n:>3}: {min_weighings(n)} weighings")
