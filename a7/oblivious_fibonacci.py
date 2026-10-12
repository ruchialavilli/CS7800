"""
Fibonacci, obliviously: compute F(n) from n so that the sequence of
operations performed is the same for every n of a given (public) bit length.
An observer watching the computation -- its timing, its power draw, which
branches it takes -- learns nothing about n except an upper bound 2^B.

Linear algebra: the recurrence F(k+1) = F(k) + F(k-1) is a linear map,

    [F(k+1)]   [1 1] [F(k)  ]            n   [F(n+1) F(n)  ]
    [F(k)  ] = [1 0] [F(k-1)]   so   Q  =   [F(n)   F(n-1)]   with Q = [1 1; 1 0].

So F(n) is a matrix power, and powers take O(log n) multiplications by
repeated squaring. Three ways to get there, each leaking less:

  1. fib_loop               n - 1 additions. The running time IS n.
  2. fib_square_multiply    square every bit, multiply only on 1-bits. O(log n)
                            but the per-bit work reveals each bit of n. This
                            is exactly how RSA keys were read off power traces
                            (simple power analysis on square-and-multiply).
  3. fib_*_ladder           Montgomery ladder: keep (Q^k, Q^(k+1)); every bit
                            does one product and two squarings, then a
                            branch-free select picks the pair. Identical work
                            for every bit, so the trace is identical for all n.

Where the lecture topics show up:
  - Strassen: a 2x2 matrix product in 7 multiplications instead of 8
    (mat_mul_strassen), dropped straight into the matrix ladder.
  - Symmetry: Q^n is determined by (F(n), F(n+1)), so the ladder only needs
    to carry two numbers. Multiplying out Q^(2k) = (Q^k)^2 gives the doubling
    formulas F(2k) = F(k)(2F(k+1) - F(k)), F(2k+1) = F(k)^2 + F(k+1)^2 --
    3 multiplications per bit (fib_doubling_ladder).
  - Eigenvalues: Q has eigenvalues phi, psi = (1 +- sqrt5)/2, which gives
    Binet's F(n) = (phi^n - psi^n)/sqrt5. In floats that breaks at n = 71.
    Exactly, phi satisfies phi^2 = phi + 1, so phi^n = F(n) phi + F(n-1) in
    the ring Z[phi]. A product in Z[phi] is a Karatsuba-style 3-multiply
    trick (golden_mul), and the same ladder runs there (fib_golden_ladder).
  - Karatsuba: the entries of Q^n have ~0.694n bits, so for big n the cost is
    dominated by integer multiplication; karatsuba() can be plugged in as the
    multiply (CPython's own int * already switches to Karatsuba for big ints).

Encryption connection: RSA, Diffie-Hellman and elliptic-curve scalar
multiplication are all "compute g^secret" -- the same exponentiation as Q^n.
The Montgomery ladder with a branch-free select is the standard defense
against timing and power side channels, and Lucas sequences (a generalized
Fibonacci) are used directly in the LUC cryptosystem and in the Lucas half of
the Baillie-PSW primality test. With a modulus m (pass mod=m) every value has
a fixed width, which is the setting where constant-time code is meaningful.

Caveat: "oblivious" here means the operation trace -- which ops, in which
order, how many per loop iteration -- is independent of n. Python big-int
arithmetic itself is not constant-time, so this demonstrates the algorithmic
structure, not a production side-channel-safe implementation.
"""

import math
import random


class Arith:
    """Integer arithmetic (optionally mod m) that records every operation it performs.

    The trace is what a side-channel observer sees: op types, plus '|' at the
    start of each loop iteration (timing/power traces show loop structure).
    Values never go in the trace.
    """

    def __init__(self, mod=None, mul=None):
        self.mod = mod
        self._mul = mul or (lambda a, b: a * b)
        self.trace = []

    def _r(self, x):
        return x % self.mod if self.mod else x

    def tick(self):
        self.trace.append("|")

    def mul(self, a, b):
        self.trace.append("*")
        return self._r(self._mul(a, b))

    def add(self, a, b):
        self.trace.append("+")
        return self._r(a + b)

    def sub(self, a, b):
        self.trace.append("-")
        return self._r(a - b)

    def select(self, bit, x, y):
        """x if bit == 0 else y, without branching: mask is 0 or all ones (-1)."""
        self.trace.append("?")
        mask = -bit
        return x ^ (mask & (x ^ y))


# ---------------------------------------------------------------- 2x2 matrices

I = ((1, 0), (0, 1))
Q = ((1, 1), (1, 0))


def mat_mul_naive(ar, X, Y):
    """8 multiplications, 4 additions."""
    (a, b), (c, d) = X
    (e, f), (g, h) = Y
    return ((ar.add(ar.mul(a, e), ar.mul(b, g)), ar.add(ar.mul(a, f), ar.mul(b, h))),
            (ar.add(ar.mul(c, e), ar.mul(d, g)), ar.add(ar.mul(c, f), ar.mul(d, h))))


def mat_mul_strassen(ar, X, Y):
    """Strassen: 7 multiplications, 18 additions/subtractions."""
    (a, b), (c, d) = X
    (e, f), (g, h) = Y
    add, sub, mul = ar.add, ar.sub, ar.mul
    m1 = mul(add(a, d), add(e, h))
    m2 = mul(add(c, d), e)
    m3 = mul(a, sub(f, h))
    m4 = mul(d, sub(g, e))
    m5 = mul(add(a, b), h)
    m6 = mul(sub(c, a), add(e, f))
    m7 = mul(sub(b, d), add(g, h))
    return ((add(sub(add(m1, m4), m5), m7), add(m3, m5)),
            (add(m2, m4), add(add(sub(m1, m2), m3), m6)))


def mat_select(ar, bit, X, Y):
    return tuple(tuple(ar.select(bit, x, y) for x, y in zip(rx, ry)) for rx, ry in zip(X, Y))


# ---------------------------------------------------------------- leaky versions

def fib_loop(n, ar):
    """Iterate the recurrence: n - 1 loop iterations, so the time reveals n."""
    a, b = 0, 1
    for _ in range(n):
        ar.tick()
        a, b = b, ar.add(a, b)
    return a


def fib_square_multiply(n, ar, matmul=mat_mul_naive):
    """Left-to-right binary powering of Q. Fast, but the multiply only happens on 1-bits."""
    R = I
    for bit in bin(n)[2:]:
        ar.tick()
        R = matmul(ar, R, R)
        if bit == "1":                       # <-- the leak
            R = matmul(ar, R, Q)
    return R[0][1]


# ---------------------------------------------------------------- oblivious versions

def bits_of(n, B):
    if not 0 <= n < 1 << B:
        raise ValueError(f"n must be in [0, 2^{B})")
    return [(n >> i) & 1 for i in reversed(range(B))]


def fib_matrix_ladder(n, B, ar, matmul=mat_mul_naive):
    """Montgomery ladder on (R0, R1) = (Q^k, Q^(k+1)); always B iterations, same work each."""
    R0, R1 = I, Q
    for bit in bits_of(n, B):
        ar.tick()
        P = matmul(ar, R0, R1)               # Q^(2k+1)
        S0 = matmul(ar, R0, R0)              # Q^(2k)
        S1 = matmul(ar, R1, R1)              # Q^(2k+2)
        R0, R1 = mat_select(ar, bit, S0, P), mat_select(ar, bit, P, S1)
    return R0[0][1]


def fib_doubling_ladder(n, B, ar):
    """The matrix ladder with Q^k stored as (F(k), F(k+1)): 3 multiplications per bit."""
    a, b = 0, 1                              # F(k), F(k+1), starting at k = 0
    for bit in bits_of(n, B):
        ar.tick()
        c = ar.mul(a, ar.sub(ar.add(b, b), a))       # F(2k)
        d = ar.add(ar.mul(a, a), ar.mul(b, b))       # F(2k+1)
        e = ar.add(c, d)                             # F(2k+2)
        a, b = ar.select(bit, c, d), ar.select(bit, d, e)
    return a


def golden_mul(ar, X, Y):
    """(x0 + x1 phi)(y0 + y1 phi) using phi^2 = phi + 1, in 3 multiplications (Karatsuba trick).

    = x0y0 + x1y1 + (x0y1 + x1y0 + x1y1) phi, and x0y1 + x1y0 = (x0+x1)(y0+y1) - x0y0 - x1y1.
    """
    (x0, x1), (y0, y1) = X, Y
    p, q = ar.mul(x0, y0), ar.mul(x1, y1)
    cross = ar.sub(ar.sub(ar.mul(ar.add(x0, x1), ar.add(y0, y1)), p), q)
    return ar.add(p, q), ar.add(cross, q)


def fib_golden_ladder(n, B, ar):
    """Ladder for phi^n in Z[phi] (the eigenvalue view); phi^n = F(n-1) + F(n) phi."""
    R0, R1 = (1, 0), (0, 1)                  # 1, phi
    for bit in bits_of(n, B):
        ar.tick()
        P, S0, S1 = golden_mul(ar, R0, R1), golden_mul(ar, R0, R0), golden_mul(ar, R1, R1)
        R0 = tuple(ar.select(bit, s, p) for s, p in zip(S0, P))
        R1 = tuple(ar.select(bit, p, s) for p, s in zip(P, S1))
    return R0[1]


# ---------------------------------------------------------------- Karatsuba, Binet

def karatsuba(x, y, cutoff=2048):
    """Karatsuba integer multiplication: 3 half-size products instead of 4."""
    if x < 0 or y < 0:
        s = -1 if (x < 0) != (y < 0) else 1
        return s * karatsuba(abs(x), abs(y), cutoff)
    if x.bit_length() <= cutoff or y.bit_length() <= cutoff:
        return x * y
    h = max(x.bit_length(), y.bit_length()) // 2
    x1, x0 = x >> h, x & ((1 << h) - 1)
    y1, y0 = y >> h, y & ((1 << h) - 1)
    hi, lo = karatsuba(x1, y1, cutoff), karatsuba(x0, y0, cutoff)
    mid = karatsuba(x1 + x0, y1 + y0, cutoff) - hi - lo
    return (hi << (2 * h)) + (mid << h) + lo


def fib_binet_float(n):
    phi, psi = (1 + math.sqrt(5)) / 2, (1 - math.sqrt(5)) / 2
    return round((phi ** n - psi ** n) / math.sqrt(5))


# ---------------------------------------------------------------- demo

def trace_of(fn, n, **kw):
    ar = Arith(**kw)
    fn(n, ar)
    return ar.trace


def per_iteration(trace):
    """Ops per loop iteration -- what a timing / power trace shows."""
    return [len(chunk) for chunk in "".join(trace).split("|")[1:]]


def spa_attack(trace, ops_per_matmul):
    """Recover n from a square-and-multiply trace: a long iteration means that bit was 1."""
    return int("".join("1" if k > ops_per_matmul else "0" for k in per_iteration(trace)), 2)


def main():
    B = 12
    ref = [0, 1]
    while len(ref) < 1 << B:
        ref.append(ref[-1] + ref[-2])

    print("1. Correctness against the plain recurrence, all n < 2^12")
    ladders = {
        "matrix ladder (naive 8-mult)": lambda n, ar: fib_matrix_ladder(n, B, ar),
        "matrix ladder (Strassen 7-mult)": lambda n, ar: fib_matrix_ladder(n, B, ar, mat_mul_strassen),
        "doubling ladder (3-mult)": lambda n, ar: fib_doubling_ladder(n, B, ar),
        "golden ladder, Z[phi] (9-mult)": lambda n, ar: fib_golden_ladder(n, B, ar),
        "square-and-multiply": fib_square_multiply,
        "loop": fib_loop,
    }
    for name, fn in ladders.items():
        ok = all(fn(n, Arith()) == ref[n] for n in range(1 << B))
        print(f"   {name:34s} {'ok' if ok else 'FAILED'}")

    m = (1 << 61) - 1
    ok = all(fib_doubling_ladder(n, B, Arith(mod=m)) == ref[n] % m for n in range(1 << B))
    print(f"   {'doubling ladder mod 2^61 - 1':34s} {'ok' if ok else 'FAILED'}")

    big = 100_003
    a = fib_doubling_ladder(big, 17, Arith())
    b = fib_doubling_ladder(big, 17, Arith(mul=karatsuba))
    print(f"   F({big:,}) has {a.bit_length():,} bits; Karatsuba multiply agrees: {a == b}")

    bad = next(n for n in range(2, 200) if fib_binet_float(n) != ref[n])
    print(f"   float Binet (phi^n - psi^n)/sqrt5 first wrong at n = {bad}; Z[phi] ladder stays exact")

    print("\n2. What leaks: distinct op traces over all 4096 inputs n < 2^12")
    print("   (1 distinct trace = the observer cannot tell any two inputs apart)")
    for name, fn in ladders.items():
        traces = {tuple(trace_of(fn, n)) for n in range(1 << B)}
        lens = [len(trace_of(fn, n)) for n in (5, 1000, 4095)]
        print(f"   {name:34s} {len(traces):5d} distinct   ops for n=5/1000/4095: {lens}")

    print("\n3. Per-iteration op counts (the 'power trace'), n = 2^11 + small changes")
    for n in (0b100000000000, 0b101101001110, 0b111111111111):
        sm = per_iteration(trace_of(fib_square_multiply, n))
        ld = per_iteration(trace_of(lambda n, ar: fib_doubling_ladder(n, B, ar), n))
        print(f"   n = {n:012b}  square-mult: {' '.join(f'{k:2d}' for k in sm)}")
        print(f"   {'':16s}  ladder:      {' '.join(f'{k:2d}' for k in ld)}")

    print("\n4. Simple power analysis: read a 64-bit secret n back off the square-and-multiply trace (mod 2^61 - 1)")
    rng = random.Random(7800)
    secrets = [rng.randrange(1, 1 << 64) for _ in range(5)]
    for s in secrets:
        got = spa_attack(trace_of(fib_square_multiply, s, mod=m), ops_per_matmul=12)
        print(f"   secret {s:20d}  recovered {got:20d}  {'MATCH' if got == s else 'miss'}")
    ladder_traces = {tuple(trace_of(lambda n, ar: fib_doubling_ladder(n, 64, ar), s, mod=m))
                     for s in secrets}
    print(f"   the same 5 secrets through the 64-bit ladder: {len(ladder_traces)} distinct trace(s)")

    print("\n5. Multiplications per bit")
    for name, fn in [("matrix ladder, naive", lambda ar: mat_mul_naive(ar, Q, Q)),
                     ("matrix ladder, Strassen", lambda ar: mat_mul_strassen(ar, Q, Q)),
                     ("golden ladder", lambda ar: golden_mul(ar, (0, 1), (0, 1)))]:
        ar = Arith()
        fn(ar)
        print(f"   {name:26s} 3 products x {ar.trace.count('*')} = {3 * ar.trace.count('*')}")
    ar = Arith()
    fib_doubling_ladder(1, 1, ar)
    print(f"   {'doubling ladder':26s} {ar.trace.count('*')}")


if __name__ == "__main__":
    main()
