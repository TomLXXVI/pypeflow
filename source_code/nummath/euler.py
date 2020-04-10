import numpy as np


class ODE:
    """
    Class for solving ODE y^o(t) = f(t, y(t), y'(t),..., y^(o-1)(t)) of order o
    using the modified Euler (based on the trapezoidal rule) or midpoint Euler method.
    """

    def __init__(self, f, y0, delta_t, n, method='MEM'):
        """
        Initialize ODE-object.

        Arguments:
        - f         function-object with signature f(t, [y, y', y",...y^(n-1)])
        - y0        list of initial values [y(0), y'(0),..., y^(o-1)(0)]
        - delta_t   time step between successive calculations of y
        - n         total number of time steps
        - method    'MEM' = Modified Euler Method (default)
                    'MPEM' = MidPoint Euler Method
        """
        self.f = f
        self.delta_t = delta_t
        self.method = method.upper()
        if self.method == 'MEM':
            self.col_size = n + 1
            self.t = np.array([k * delta_t for k in range(self.col_size)])
        elif self.method == 'MPEM':
            self.col_size = 2 * n + 1
            self.t = np.array([k * delta_t / 2 for k in range(self.col_size)])
        self.row_size = len(y0) + 1
        self.y = np.empty((self.row_size, self.col_size))
        self.y[:-1, 0] = y0
        self.y[-1, 0] = self.f(0, y0)

    def solve(self):
        """
        Solve ODE.

        Return value:
        Tuple (t, y) with:
        - t     (1 x n) numpy array with time
        - y     (o x n) numpy array containing the solutions y(t), y'(t)...y^(o)(t)
        """
        if self.method == 'MEM':
            self._solve_MEM()
        elif self.method == 'MPEM':
            self._solve_MPEM()
        return self.t, self.y

    def _solve_MEM(self):
        """Solve ODE with the Modified Euler Method (MEM)."""
        for k in range(1, self.col_size):
            # first, predict with forward Euler method
            for r in range(self.row_size):
                if r < self.row_size - 1:
                    self.y[r, k] = self.y[r, k - 1] + self.delta_t * self.y[r + 1, k - 1]
                elif r == self.row_size - 1:
                    self.y[r, k] = self.f(self.t[k], self.y[:-1, k])
            # next, correct with trapezoidal rule
            for r in range(self.row_size - 1):
                self.y[r, k] = self.y[r, k - 1] + 0.5 * self.delta_t * (self.y[r + 1, k - 1] + self.y[r + 1, k])

    def _solve_MPEM(self):
        """Solve ODE with the MidPoint Euler Method (MPEM)."""
        for k in range(1, self.col_size):
            if k % 2 == 1:
                for r in range(self.row_size):
                    if r < self.row_size - 1:
                        self.y[r, k] = self.y[r, k - 1] + self.delta_t / 2 * self.y[r + 1, k - 1]
                    elif r == self.row_size - 1:
                        self.y[r, k] = self.f(self.t[k], self.y[:-1, k])
            elif k % 2 == 0:
                for r in range(self.row_size):
                    if r < self.row_size - 1:
                        self.y[r, k] = self.y[r, k - 2] + self.delta_t * self.y[r + 1, k - 1]
                    elif r == self.row_size - 1:
                        self.y[r, k] = self.f(self.t[k], self.y[:-1, k])
        self.t = self.t[[i for i in range(self.col_size) if i % 2 == 0]]
        self.y = self.y[:, [i for i in range(self.col_size) if i % 2 == 0]]


class LDE1:
    """
    First order linear differential equation: y'(t) + a.y(t) = f(t)
    """
    def __init__(self, f, a, y0, delta_t, n):
        self.f = f
        self.a = a
        self.delta_t = delta_t
        self.n = n  # number of time steps
        self.t = np.array([k * delta_t for k in range(self.n + 1)])
        self.y = np.empty(self.n + 1)
        self.y[0] = y0

    def solve(self):
        for k in range(1, self.n + 1):
            s = self.y[k - 1] + (self.delta_t / 2) * (self.f(self.t[k - 1]) - self.a * self.y[k - 1])
            self.y[k] = (self.f(self.t[k]) * self.delta_t + 2 * s) / (self.a * self.delta_t + 2)
        return self.t, self.y


class LDE2:
    """
    Second order linear differential equation: y"(t) + a1.y'(t) + a0.y = f(t)
    """
    def __init__(self, f, a, y0, delta_t, n):
        self.f = f
        self.a = a
        self.delta_t = delta_t
        self.n = n  # number of time steps
        self.t = np.array([k * delta_t for k in range(self.n + 1)])
        self.y = np.empty((2, self.n + 1))
        self.y[:, 0] = y0

    def solve(self):
        for k in range(1, self.n + 1):
            s0 = self.y[0, k - 1] + 0.5 * self.delta_t * self.y[1, k - 1]
            s1 = self.y[1, k - 1] + 0.5 * self.delta_t * (self.f(self.t[k - 1]) - self.a[1] * self.y[1, k - 1] -
                                                          self.a[0] * self.y[0, k - 1])
            self.y[1, k] = ((2 * (self.f(self.t[k]) - self.a[0] * s0) * self.delta_t + 4 * s1) /
                            (self.a[0] * self.delta_t ** 2 + 2 * self.a[1] * self.delta_t + 4))
            self.y[0, k] = s0 + 0.5 * self.delta_t * self.y[1, k]
        return self.t, self.y


def ode_print(t, y, freq=1):
    """
    Print the solutions of an ODE in columns ( t   y   y'  ... y^(n)   )
    Params:
        - t     array with 't' values
        - y     matrix with 'y' values [y, y', y",...] at each 't'
        - freq  the step between lines
    """

    def print_heading(n):
        print("t".center(13), end=" ")
        for i in range(n):
            print(f"y[{i}]".center(13), end=" ")
        print()

    # noinspection PyShadowingNames
    def print_line(t, y, n):
        print(f"{t:.4f}".rjust(13), end=" ")
        for i in range(n):
            print(f"{y[i]:.4f}".rjust(13), end=" ")
        print()

    row_num = y.shape[0]
    col_num = y.shape[1]

    print_heading(row_num)

    for k in range(0, col_num, freq):
        print_line(t[k], y[:, k], row_num)
