import cmath
from random import random

import numpy as np


class Polynomial:
    def __init__(self, a):
        """
        Define the polynomial 'p = a[0] + a[1]*x + a[2]*x^2 + ... + a[n]*x^n'.
        Params:
            - a     array with the coefficients of the polynomial
        """
        self._a = a
        self.a = np.copy(a)

    def eval(self, x, tol=1.0e-12):
        """
        Evaluate the polynomial 'p = a[0] + a[1]*x + a[2]*x^2 + ... + a[n]*x^n' at 'x'.
        Params:
            - x     point where the polynomial is to be evaluated
        Return values:
            - p     the value of the polynomial at 'x'
            - dp    the value of the first derivative of the polynomial at 'x'
            - ddp   the value of the second derivative of the polynomial at 'x'
        """
        self._a = self.a
        L = list(self._eval(x))
        for i in range(len(L)):
            if abs(L[i].imag) < tol:
                L[i] = L[i].real
        return L

    def _eval(self, x):
        n = len(self._a) - 1
        p = self._a[n]
        dp = 0.0 + 0.0j
        ddp = 0.0 + 0.0j
        for i in range(1, n + 1):
            ddp = ddp * x + 2.0 * dp
            dp = dp * x + p
            p = p * x + self._a[n - i]
        return p, dp, ddp

    def _laguerre(self, x, tol):
        n = len(self._a) - 1
        for i in range(30):
            p, dp, ddp = self._eval(x)
            if abs(p) < tol:
                return x
            g = dp / p
            h = g * g - ddp / p
            f = cmath.sqrt((n - 1) * (n * h - g * g))
            if abs(g + f) > abs(g - f):
                dx = n / (g + f)
            else:
                dx = n / (g - f)
            x = x - dx
            if abs(dx) < tol:
                return x
        raise OverflowError('too many iterations')

    def _deflate(self, root):
        n = len(self._a) - 1
        b = [(0.0 + 0.0j)] * n
        b[n - 1] = self._a[n]
        for i in range(n - 2, -1, -1):
            b[i] = self._a[i + 1] + root * b[i + 1]
        return b

    def roots(self, tol=1.0e-12, roots_guess=None):
        """
        Uses Laguerre's method to compute all the roots of 'a[0] + a[1]*x + a[2]*x^2 + ... + a[n]*x^n = 0', which
        can be real or complex.
        Params:
            - tol           error tolerance (a value less than 'tol' is considered as zero)
            - roots_guess   initial guess values for the roots; if None (default), random guesses will be used
                            (note: a polynomial of order n, has n roots)
        Return value:
            - array with the roots of the polynomial
        """
        self._a = self.a
        n = len(self._a) - 1
        roots = np.zeros(n, dtype=complex)
        for i in range(n):
            if roots_guess is not None:
                x = roots_guess[i]
            else:
                x = random()
            x = self._laguerre(x, tol)
            if abs(x.imag) < tol:
                x = x.real
            roots[i] = x
            self._a = self._deflate(x)
        return roots
