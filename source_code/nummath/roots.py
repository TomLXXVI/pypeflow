"""Finding the roots of an equation f(x) = 0."""

import nummath.linear_system as linear_system
import numpy as np


class FunctionRootSolver:
    """
    Find the roots of function f(x) in a given search area on the x-axis.
    """
    def __init__(self, f, search_area, search_step, method='bisection', deriv1_f=None):
        """
        Initialize FunctionRootSolver instance.
        - f             the name of the function the root(s) need to be looked for; the function should be of the form
                        "def f(x):... return y" (function rule with one variable 'x' that returns 'y')
        - search_area   the interval on the x-axis to search in, given as a list [x_start, x_end]
        - search_step   the step size for stepping through the search area (rough incremental search)
        - method        the method to be used to find the roots: 'bisection' (default), 'ridder' or 'newton-raphson'
        - deriv1_f      the first derivative of f; only to be used with Newton-Raphson method;
                        the function should be of the form "def deriv1_f(x):... return df" (function rule with one
                        variable 'x' that returns the first derivative 'df' at 'x')
        """
        self._f = f
        self._search_area = search_area
        self._search_step = search_step
        self._tolerance = 1.0e-9
        self._check = False
        self._roots = []
        self._method_str = method.lower()
        if self._method_str == 'bisection':
            self._method = self._bisection
        if self._method_str == 'ridder':
            self._method = self._ridder
        if self._method_str == 'newton-raphson':
            self._method = self._newton_raphson
            self._deriv1_f = deriv1_f

    @property
    def tolerance(self):
        """
        Return the smallest interval that stops the search routine.
        """
        return self._tolerance

    @tolerance.setter
    def tolerance(self, tol):
        """
        Set the smallest interval that stops the search routine.
        Eg. if tol=1.0e-4 (0.0001) the returned result of the root has a four-digit accuracy.
        """
        self._tolerance = tol

    @property
    def check_search(self):
        """
        Return 'True' if the search routine does a check on the search results; otherwise return 'False'.
        """
        return self._check

    @check_search.setter
    def check_search(self, bool_):
        """
        Enter 'True' if the search routine has to check the intermediary search results.
        The routine checks whether the magnitude of f(x) decreases with each interval halving;
        if it does not, something may be wrong (probably the root is not a root but a pole).
        """
        self._check = bool_

    @property
    def roots(self):
        """
        Return the roots.
        """
        return self._roots

    def _incremental_search(self):
        """
        Step through the given search area looking for a change of sign of the function (which means the function
        has crossed a zero).
        If there is a change in sign between two output values y (which are one step apart), the start (x_start)
        and end point (x_end) of the last step location are returned. If the end of the search area is reached return
        None.
        """
        x_start = self._search_area[0]
        y_start = self._f(x_start)
        x_end = x_start + self._search_step; y_end = self._f(x_end)
        while np.sign(y_start) == np.sign(y_end):
            if x_start >= self._search_area[1]:
                return None  # end of search area has been crossed
            x_start = x_end; y_start = y_end
            x_end = x_start + self._search_step; y_end = self._f(x_end)
        else:
            return x_start, x_end

    def _bisection(self, bracket):
        """
        Find a root of f(x) = 0 by bisection (the bracket around the root is made smaller and smaller).
        """
        x_1 = bracket[0]; y_1 = self._f(x_1)
        if y_1 == 0.0:
            return x_1
        x_2 = bracket[1]; y_2 = self._f(x_2)
        if y_2 == 0.0:
            return x_2
        # calculate the number of bisections required to reach the tolerance
        n = int(np.ceil(np.log(abs(x_2 - x_1) / self._tolerance) / np.log(2)))
        for i in range(n):
            x_3 = 0.5 * (x_1 + x_2); y_3 = self._f(x_3)
            if self._check and (abs(y_3) > abs(y_1)) and (abs(y_3) > abs(y_2)):
                return None  # something's wrong, probably the 'root' is not a root but a pole
            if y_3 == 0.0:
                return x_3
            if np.sign(y_2) != np.sign(y_3):
                x_1 = x_3; y_1 = y_3
            else:
                x_2 = x_3; y_2 = y_3
        return (x_1 + x_2) / 2

    def _ridder(self, bracket):
        """
        Find a root of f(x) = 0 with Ridder's method.
        """
        x_1 = bracket[0]; y_1 = self._f(x_1)
        if y_1 == 0.0:
            return y_1
        x_2 = bracket[1]; y_2 = self._f(x_2)
        if y_2 == 0.0:
            return y_2
        for i in range(30):
            x_3 = (x_1 + x_2) / 2; y_3 = self._f(x_3)
            if self._check and (abs(y_3) > abs(y_1)) and (abs(y_3) > abs(y_2)):
                return None  # something's wrong, probably the 'root' is not a root but a pole
            s = np.sqrt(y_3**2 - y_1 * y_2)
            if s == 0.0:
                return None
            d_x = (x_3 - x_1) * y_3 / s
            if y_1 - y_2 < 0.0:
                d_x = - d_x
            x = x_3 + d_x; y = self._f(x)
            if i > 0:
                # test for convergence
                # noinspection PyUnboundLocalVariable
                if abs(x - x_old) < self._tolerance * max(abs(x), 1.0):
                    return x
            x_old = x
            if np.sign(y_3) == np.sign(y):
                if np.sign(y_1) != np.sign(y):
                    x_2 = x; y_2 = y
                else:
                    x_1 = x; y_1 = y
            else:
                x_1 = x_3; y_1 = y_3
                x_2 = x; y_2 = y

    def _newton_raphson(self, bracket):
        """
        Find a root of f(x) = 0 with Newton-Raphson method.
        """
        x_1 = bracket[0]; y_1 = self._f(x_1)
        if y_1 == 0.0:
            return y_1
        x_2 = bracket[1]; y_2 = self._f(x_2)
        if y_2 == 0.0:
            return y_2
        x = 0.5 * (x_1 + x_2)
        for i in range(30):
            y = self._f(x)
            if y == 0.0:
                return x
            if np.sign(y_1) != np.sign(y):
                x_2 = x
            else:
                x_1 = x
            y_der1 = self._deriv1_f(x)
            # if division by zero, push new x out of bracket
            try:
                dx = - y / y_der1
            except ZeroDivisionError:
                dx = x_2 - x_1
            x += dx
            if (x_2 - x) * (x - x_1) < 0.0:  # if the result x is outside the brackets, use bisection
                dx = 0.5 * (x_2 - x_1)
                x = x_1 + dx
            if abs(dx) < self._tolerance * max(abs(x_2), 1.0):
                return x

    def solve(self):
        """
        Return all the roots in the given search area.
        """
        while True:
            bracket = self._incremental_search()
            if bracket:
                root = self._method(bracket)
                if root is not None: self._roots.append(root)
                self._search_area[0] = bracket[1]
            else:
                break
        return self._roots


class SystemRootSolver:
    """
    Solving n simultaneous, nonlinear equations in n unknowns using the Newton-Raphson method.
    """
    def __init__(self, f_array, x_array):
        """
        Initialize SystemRootSolver instance.
        Params:
        - f_array   array of function objects constituting the system of equations
        - x_array   array with initial guesses for the unknown x'es
        """
        def f(x):
            f_vector = np.zeros(len(x))
            for i, f_ in enumerate(f_array):
                f_vector[i] = f_(x)
            return f_vector

        self._f = f
        self._x = x_array
        n = len(self._x)
        self._jac = np.zeros((n, n))
        self._y_0 = self._f(self._x)
        self._tolerance = 1.0e-9

    @property
    def tolerance(self):
        """
        Return the smallest deviation that stops the solving routine.
        """
        return self._tolerance

    @tolerance.setter
    def tolerance(self, tol):
        """
        Set the smallest deviation that stops the solving routine.
        """
        self._tolerance = tol

    def _jacobian(self):
        h = 1.0e-4
        n = len(self._x)
        for i in range(n):
            temp = self._x[i]
            self._x[i] = temp + h
            y_1 = self._f(self._x)
            self._x[i] = temp
            self._jac[:, i] = (y_1 - self._y_0) / h

    def solve(self):
        for i in range(30):
            self._jacobian()
            if np.sqrt(np.dot(self._y_0, self._y_0) / len(self._x)) < self._tolerance:
                return self._x.flatten()
            delta_x = linear_system.GaussElimin(self._jac, -self._y_0, pivot_on=True).solve()
            self._x += delta_x
            if np.sqrt(np.dot(delta_x, delta_x)) < self._tolerance * max(max(abs(self._x)), 1.0):
                return self._x.flatten()
        raise OverflowError('too many iterations')
