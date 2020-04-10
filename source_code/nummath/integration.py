import numpy as np


class SingleIntegration:
    def __init__(self, f, a, b):
        """
        Initialize integration solver.
        Params:
            - f     name of the function to be integrated which must have a signature 'def f(x):...return f_x'
            - a     start point x=a of integration interval
            - b     end point x=b of integration interval
        """
        self.f = f
        self.a = a
        self.b = b

    def _trap_rule(self, x, h):
        """
        Trapezoidal rule.
        Calculate the area of the strip bounded by the interval ['x', 'x'+'h'] and [f('x'), f('x' + 'h')].
        Note: the function f between 'x' and 'x + h' is approximated by a straight line.
        Params:
            - x   start point of the interval
            - h   width of the interval
        Return value:
            - area under the strip
        """
        return (self.f(x) + self.f(x + h)) * (h / 2.0)

    def _recursive_trap_rule(self, I_old, k):
        """
        Recursive trapezoidal rule.
        Params:
            - I_old     previous solution of the integral dividing the integration interval [a, b] into 2^(k-2) strips
            - k         set the number of strips to 2^(k-1) for the new solution of the integral
        Return value:
            - new solution for the integral with the number of strips doubled
        """
        if k == 1:
            I_new = self._trap_rule(self.a, self.b - self.a)
        else:
            n = 2**(k - 2)
            h = (self.b - self.a) / n
            x = self.a + h / 2.0
            sum_ = 0.0
            for i in range(n):
                sum_ = sum_ + self.f(x)
                x += h
            I_new = (I_old + h * sum_) / 2.0
        return I_new

    @staticmethod
    def _richardson(r, k):
        """
        Richardson extrapolation. Helper method of '_romberg'.
        """
        for j in range(k - 1, 0, -1):
            const = 4.0 ** (k - j)
            r[j] = (const * r[j + 1] - r[j]) / (const - 1.0)
        return r

    def _romberg(self, tol=1.0e-6):
        """
        Romberg quadrature.
        Combines the recursive trapezoidal rule with Richardson extrapolation.
        """
        r = np.zeros(21)
        r[1] = self._recursive_trap_rule(0.0, 1)
        r_old = r[1]
        for k in range(2, 21):
            r[k] = self._recursive_trap_rule(r[k - 1], k)
            r = self._richardson(r, k)
            if abs(r[1] - r_old) < tol * max(abs(r[1]), 1.0):
                return r[1], 2 ** (k - 1)
            r_old = r[1]
        raise OverflowError("Romberg quadrature did not converge")

    def solve(self, tol=1.0e-6):
        """
        Solve the integral using Romberg quadrature.
        Params:
            - tol   accuracy in decimal places of the solution (the calculation is repeated until the difference between
                    the new solution and the old solution is smaller than 'tol')
        Return value:
            - the integral of f(x) between x=a and x=b
            - the number of strips used to calculate the integral
        """
        return self._romberg(tol)
