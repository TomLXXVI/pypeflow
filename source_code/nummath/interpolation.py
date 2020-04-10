"""Interpolation and curve fitting."""

import nummath.graphing as graphing
import nummath.linear_system as lin_sys
import numpy as np


# ---------------------------------------------------------------------------------------------------------------------
# Interpolation


class _InterPol:
    def __init__(self, x_data, y_data):
        self._x_data = np.array(x_data, dtype=np.float64)
        self._y_data = np.array(y_data, dtype=np.float64)

    def solve(self, x):
        pass


class PolyInterPol(_InterPol):
    """
    Polynomial (n-degree) interpolation using Newton's method or Neville's method (default is Newton).
    The number of data points determines the degree of the polynomial.
    """
    def __init__(self, x_data, y_data, method="newton"):
        """
        Initialize.
        Params:
        - x_data    x-coordinates of data points (as list or Numpy array)
        - y_data    y-coordinates of data points (as list or Numpy array)
        - method    the method for doing the interpolation: newton (= default) or neville

        Note: Newton's method is preferred if the interpolation needs to be done at multiple points.
        If only one point is to be interpolated, Neville's algorithm is more efficient.
        """
        super().__init__(x_data, y_data)
        self._method = method.lower()

        if self._method == "newton":
            self._a = self._y_data.copy()     # initialize polynomial coefficient array with y_data
            self._calc_newton_coefficients()  # calculate polynomial coefficients

    def _calc_newton_coefficients(self):
        m = len(self._x_data)
        for k in range(1, m):
            self._a[k:m] = (self._a[k:m] - self._a[k - 1]) / (self._x_data[k:m] - self._x_data[k - 1])

    def _newton(self, x):
        n = len(self._x_data) - 1
        y = self._a[n]
        for k in range(1, n + 1):
            y = self._a[n - k] + (x - self._x_data[n - k]) * y
        return y

    def _neville(self, x):
        m = len(self._x_data)
        y = self._y_data.copy()
        for k in range(1, m):
            y[0:m - k] = (((x - self._x_data[k:m]) * y[0:m - k] + (self._x_data[0:m - k] - x) * y[1:m - k + 1]) /
                          (self._x_data[0:m - k] - self._x_data[k:m]))
        return y[0]

    def solve(self, x):
        """
        Get corresponding y-coordinate on polynomial for given x-coordinate.
        Note: If Neville's method is used only one value for x must be passed. In case of Newton's method a list of
        multiple x values can be passed.
        """
        if self._method == "neville":
            y = self._neville(x)
        else:
            y = self._newton(x)
        return y


class RatInterPol(_InterPol):
    """
    Rational interpolation.
    Data is interpolated using a diagonal rational function.
    """
    def solve(self, x):
        m = len(self._x_data)
        r = self._y_data.copy()
        r_old = np.zeros(m)
        for k in range(m - 1):
            for i in range(m - k - 1):
                if abs(x - self._x_data[i + k + 1]) < 1.0e-9:
                    return self._y_data[i + k + 1]
                else:
                    c1 = r[i + 1] - r[i]
                    c2 = r[i + 1] - r_old[i + 1]
                    c3 = (x - self._x_data[i]) / (x - self._x_data[i + k + 1])
                    r[i] = r[i + 1] + c1 / (c3 * (1.0 - c1 / c2) - 1.0)
                    r_old[i + 1] = r[i + 1]
        return r[0]


class CubicSplineInterPol(_InterPol):
    """
    Data is interpolated using a natural cubic spline (second derivative in endpoints of spline is 0).
    """
    def __init__(self, x_data, y_data):
        super().__init__(x_data, y_data)
        self._curvature()

    def _curvature(self):
        n = len(self._x_data) - 1
        c = np.zeros(n)
        d = np.ones(n + 1)
        e = np.zeros(n)
        b = np.zeros(n + 1)

        c[0:n - 1] = self._x_data[0:n - 1] - self._x_data[1:n]
        d[1:n] = 2.0 * (self._x_data[0:n - 1] - self._x_data[2:n + 1])
        e[1:n] = self._x_data[1:n] - self._x_data[2:n + 1]
        b[1:n] = 6.0 * ((self._y_data[0:n - 1] - self._y_data[1:n]) / (self._x_data[0:n - 1] - self._x_data[1:n]) -
                        (self._y_data[1:n] - self._y_data[2:n + 1]) / (self._x_data[1:n] - self._x_data[2:n + 1]))
        self._k = lin_sys.B3DLinSys(c, d, e, b).solve()

    def _find_segment(self, x):
        index_left = 0
        index_right = len(self._x_data) - 1
        while True:
            if (index_right - index_left) <= 1:
                return index_left
            index = (index_left + index_right) // 2
            if x < self._x_data[index]:
                index_right = index
            else:
                index_left = index

    def solve(self, x):
        i = self._find_segment(x)
        h = self._x_data[i] - self._x_data[i + 1]
        y = ((self._k[i] / 6) * ((x - self._x_data[i + 1]) ** 3 / h - (x - self._x_data[i + 1]) * h) -
             (self._k[i + 1] / 6) * ((x - self._x_data[i]) ** 3 / h - (x - self._x_data[i]) * h) +
             (self._y_data[i] * (x - self._x_data[i + 1]) - self._y_data[i + 1] * (x - self._x_data[i])) / h)
        return y


# ---------------------------------------------------------------------------------------------------------------------
# Curve fitting


class _CurveFit:
    # Base class for curve fitting
    def __init__(self, x_data, y_data):
        self._x_data = np.array(x_data, dtype=np.float64)
        self._y_data = np.array(y_data, dtype=np.float64)
        self._c = None  # will point to the computed coefficients of the fitting curve
        self._solved = False

    def solve(self):
        """
        Returns the coefficients of the polynomial.
        """
        # override in specialised curve fitting class
        pass

    def eval_fitting_curve_single(self, x):
        """
        Calculate y = f(x) at given single x.
        """
        # override in specialised curve fitting class
        pass

    def eval_fitting_curve_multi(self, x_array):
        """
        Calculate y = f(x) for multiple values of x.
        """
        # override in specialised curve fitting class
        pass

    def std_dev(self):
        """
        Return standard deviation (quantifies the spread of the data about the fitting curve).
        """
        if self._solved:
            n = len(self._x_data) - 1
            m = len(self._c) - 1
            sigma = 0.0
            for i in range(n + 1):
                y = self.eval_fitting_curve_single(self._x_data[i])
                sigma += (self._y_data[i] - y)**2
            sigma = np.sqrt(sigma / (n - m))
            return sigma

    def plot(self, x_title='x', y_title='y', fig_size=None, dpi=None):
        """
        Show data points and fitting curve in a graph.
        """
        if self._solved:
            # calculate some points on the fitting curve
            x = np.linspace(np.min(self._x_data), np.max(self._x_data), 21, endpoint=True)
            y = self.eval_fitting_curve_multi(x)
            # show the data points and the calculated points in a graph
            g = graphing.Graph(fig_size=fig_size, dpi=dpi)
            g.add_data_set('data', self._x_data, self._y_data, marker='o', linestyle='None')
            g.add_data_set('curve fit', x, y)
            g.set_axis_titles(x_title, y_title)
            g.draw_graph()
            g.show_graph()


class PolyFit(_CurveFit):
    """
    Polynomial Fitting (fitting data with a polynomial function "f(x) = c0 + c1.x + c2.x^2 + ... + cm.x^m").
    The goal is to find the coefficients c0...cm of the polynomial using least-squares fit.
    """
    def __init__(self, x_data, y_data, m):
        """
        Initialize.
        Params:
        - x_data    x-coordinates of data points as list
        - y_data    y-coordinates of data points as list
        - m         the degree of the polynomial to be fitted to the n data points

        Note: Polynomials of high order (> 6) are not recommended, because they tend to reproduce the noise inherent in
        the measurement data.
        """
        super().__init__(x_data, y_data)
        self._m = m
        self._a = np.zeros((self._m + 1, self._m + 1))
        self._b = np.zeros(self._m + 1)
        self._s = np.zeros(2 * self._m + 1)
        self._c = np.zeros(self._m + 1)  # coefficients c of polynomial with degree m
        self._build_matrix_equation()

    def _build_matrix_equation(self):
        for i in range(len(self._x_data)):
            # build input vector b
            temp = self._y_data[i]
            for j in range(len(self._b)):
                self._b[j] += temp
                temp *= self._x_data[i]
            # calculate the elements in the coefficient matrix a
            temp = 1.0
            for j in range(len(self._s)):
                self._s[j] += temp
                temp *= self._x_data[i]
        # build coefficient matrix (= symmetric matrix)
        for i in range(self._m + 1):
            for j in range(self._m + 1):
                self._a[i, j] = self._s[i + j]

    def solve(self):
        self._c = lin_sys.GaussElimin(self._a, self._b, pivot_on=True).solve()
        self._solved = True
        return self._c.flatten()

    def eval_fitting_curve_single(self, x):
        if self._solved:
            m = len(self._c) - 1
            y = self._c[m]
            for j in range(m):
                y = y * x + self._c[m - j - 1]
            return y

    def eval_fitting_curve_multi(self, x_array):
        if self._solved:
            y = np.zeros(len(x_array))
            for i in range(len(x_array)):
                y[i] = self.eval_fitting_curve_single(x_array[i])
            return y


class LinReg(_CurveFit):
    """
    Linear Regression (fitting data with straight line "f(x) = c0 + c1.x").
    The goal is to find the coefficients c0 and c1 of the straight line using least-squares fit.
    """
    def __init__(self, x_data, y_data):
        super().__init__(x_data, y_data)
        self._mean_x = np.mean(self._x_data)
        self._mean_y = np.mean(self._y_data)
        self._c = np.zeros(2)

    def solve(self):
        """
        Returns the coefficients a and b of the straight line.
        """
        self._c[1] = (np.sum(self._y_data * (self._x_data - self._mean_x)) /
                      np.sum(self._x_data * (self._x_data - self._mean_x)))
        self._c[0] = self._mean_y - self._mean_x * self._c[1]
        self._solved = True
        return self._c

    def eval_fitting_curve_single(self, x):
        if self._solved:
            return self._c[0] + self._c[1] * x

    def eval_fitting_curve_multi(self, x_array):
        if self._solved:
            return self._c[0] + self._c[1] * x_array


class ExpFit(_CurveFit):
    """
    Exponential Fitting (fitting data with exponential function "f(x) = c0.e^(c1.x)").
    The goal is to find the coefficients c0 and c1 of the exponential function using least-squares fit.
    """
    # y = c0.e^(c1.x) ==> ln(y) = ln(c0) + c1.x is a straight line and we can use linear regression to find ln(c0) and
    # c1; afterwards we determine c0 from c0 = exp(ln(c0))
    # the algorithm uses weighting coefficients wi = yi for the least-squares fit.
    def __init__(self, x_data, y_data):
        super().__init__(x_data, y_data)
        self._lny_data = np.log(self._y_data)
        self._weights = self._y_data
        self._w_avg_x = np.average(self._x_data, weights=self._weights**2)
        self._w_avg_lny = np.average(self._lny_data, weights=self._weights ** 2)
        self._c = np.zeros(2)

    def solve(self):
        self._c[1] = (np.sum(self._weights**2 * self._lny_data * (self._x_data - self._w_avg_x)) /
                      np.sum(self._weights**2 * self._x_data * (self._x_data - self._w_avg_x)))
        self._c[0] = np.exp(self._w_avg_lny - self._c[1] * self._w_avg_x)
        self._solved = True
        return self._c

    def eval_fitting_curve_single(self, x):
        if self._solved:
            return self._c[0] * np.exp(self._c[1] * x)

    def eval_fitting_curve_multi(self, x_array):
        if self._solved:
            return self._c[0] * np.exp(self._c[1] * x_array)
