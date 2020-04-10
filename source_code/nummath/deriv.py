import numpy as np


class Deriv:
    """
    Calculate the derivative with given order of the function f(t) at point t.
    """
    def __init__(self, f, dt, o=1):
        """
        Initialize the differentiation solver.
        Params:
            - f         the name of the function object ('def f(t):...')
            - dt        the calculation step between successive points
            - o         the order of the derivative to be calculated
        """
        self.f = f
        self.dt = dt
        self.o = o

        # coefficients of forward finite difference approximations of order O(h^2)
        self.co = np.array([
            [-3.0, 4.0, -1.0, 0.0, 0.0, 0.0],
            [2.0, -5.0, 4.0, -1.0, 0.0, 0.0],
            [-5.0, 18.0, -24.0, 14.0, -3.0, 0.0],
            [3.0, -14.0, 26.0, -24.0, 11.0, -2.0]
        ])
        self.den = np.array([2 * dt, dt ** 2, 2 * dt ** 3, dt ** 4])

    def solve(self, t):
        """
        Calculate the derivative at point 't'.
        The method uses Richardson extrapolation to improve accuracy.
        """
        df = [0.0, 0.0]
        for i, dt_ in enumerate([self.dt, self.dt / 2]):
            t_array = np.arange(t, t + 6 * dt_, dt_)
            f_array = np.array([self.f(t_i) for t_i in t_array])
            c_array = self.co[self.o - 1, :]
            df[i] = (c_array * f_array) / self.den[self.o - 1]
        return (4.0 * df[1] - df[0]) / 3.0
