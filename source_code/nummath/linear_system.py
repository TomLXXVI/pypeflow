"""Solving systems of linear algebraic equations."""
import numpy as np


class Swap:
    """Swap rows or columns in a matrix or vector."""
    @staticmethod
    def swap_rows(m, i, j):
        if len(m.shape) == 1:  # m is a vector
            m[i], m[j] = m[j], m[i]
        else:
            m[[i, j], :] = m[[j, i], :]

    @staticmethod
    def swap_cols(m, i, j):
        m[:, [i, j]] = m[:, [j, i]]


class _LinSys:
    def __init__(self, a, b, tol=1.0e-12, pivot_on=False, dtype=np.float64):
        """
        Initialize linear system.
        Params:
        - a         coefficient matrix
        - b         input vector
        - tol       rounding tolerance, i.e. the smallest value that is considered as zero (default is 1.0e-12)
        - pivot_on  turn row pivoting on (True) or off (False) (default is off)
        """
        self._a_original = a
        self._a = np.copy(a)
        self._b = b
        self._x = np.empty(self._b.shape, dtype=dtype)
        self._det_a = None
        self._solved = False
        self._row_scf = np.empty(len(self._b), dtype=dtype)  # array with scale factor for each row of a
        self._tol = tol
        self._pivot_on = pivot_on
        if self._pivot_on: self._calc_row_scf()

    def _calc_row_scf(self):
        # Calculate scale factors for row pivoting. The scale factor of a row is the largest absolute value in a row.
        n = len(self._b)
        for i in range(n):
            self._row_scf[i] = np.max(np.abs(self._a[i, :]))

    def _row_pivot(self, col_index):
        # Perform row pivoting. Interchange rows if there is a better pivot element than the current one.
        n = len(self._a)
        k = col_index
        rel_vals = np.abs(self._a[k:n, k] / self._row_scf[k:n])  # array w. relative absolute values of cls._a[k:n, k]
        p = k + np.argmax(rel_vals)  # index of largest rel. value in col. k of matrix cls._a
        self._check_with_tolerance(self._a[p, k])  # if too close to zero, the matrix will be singular (det a = 0)
        if p != k:  # if cls._a[k, k] hasn't the largest rel. value, swap rows
            Swap.swap_rows(self._b, k, p)
            Swap.swap_rows(self._row_scf, k, p)
            Swap.swap_rows(self._a, k, p)

    def _check_with_tolerance(self, elem):
        # If during transformation (elimination or decomposition) of cls._a a diagonal el. is too close to zero,
        # it means that the coefficient matrix will be singular, i.e. there will be no unique solution.
        if abs(elem) < self._tol:
            raise ValueError("matrix is singular")

    def solve(self):
        """Solve linear system."""
        pass

    @staticmethod
    def _determinant(tri_mat):
        """Calculate determinant of triangular matrix."""
        return np.diagonal(tri_mat).prod()

    @property
    def det(self):
        """Return determinant of coefficient matrix a."""
        return

    @property
    def euclidian_norm(self):
        """Calculate Euclidian norm of coefficient matrix."""
        return np.sqrt(np.sum(np.power(self._a_original.flatten(), 2)))

    @property
    def infinity_norm(self):
        """Calculate infinity norm of coefficient matrix."""
        n = len(self._a_original)
        max_ = -1.0
        for i in range(n):
            s = np.sum(np.abs(self._a_original[i, :]))
            if s > max_: max_ = s
        return max_

    @property
    def a_orig(self):
        """Return original coefficient matrix."""
        return self._a_original

    @property
    def a(self):
        """Return transformed coefficient matrix."""
        return self._a

    @property
    def b(self):
        """Return input vector."""
        return self._b

    @property
    def x(self):
        """Return solution vector."""
        return self._x


class GaussElimin(_LinSys):
    """
    Solve linear system with Gauss Elimination Method.
    The solving method supports row pivoting.
    """
    def __init__(self, a, b, tol=1.0e-12, pivot_on=False, dtype=np.float64):
        super().__init__(a, b, tol=tol, pivot_on=pivot_on, dtype=dtype)
        self._eliminated = False

    def _eliminate(self):
        """Transform coefficient matrix to upper triangular matrix."""
        n = len(self._a)
        for k in range(n-1):  # index k points to the 'pivot row' and 'pivot column'
            if self._pivot_on: self._row_pivot(k)
            for i in range(k+1, n):
                if self._a[i, k] != 0.0:
                    lambda_ = self._a[i, k] / self._a[k, k]
                    self._a[i, k:n] -= lambda_ * self._a[k, k:n]
                    self._b[i] -= lambda_ * self._b[k]
        self._check_with_tolerance(self._a[n - 1, n - 1])
        self._eliminated = True

    def _backward_substitute(self):
        n = len(self._a)
        for k in range(n-1, -1, -1):
            self._x[k] = (self._b[k] - np.dot(self._a[k, k + 1:n], self._x[k + 1:n])) / self._a[k, k]

    def solve(self):
        if not self._solved:
            if not self._eliminated: self._eliminate()
            self._backward_substitute()
            self._solved = True
        return self._x.flatten()

    @property
    def det(self):
        if not self._eliminated: self._eliminate()
        if not self._det_a: self._det_a = self._determinant(self._a)
        return self._det_a


class LUDecomp(_LinSys):
    """
    Solve linear system with LU-Decomposition Methods (Doolittle or Choleski).
    Note 1: Choleski's method is limited to symmetric and positive definite coefficient matrices.
    Note 2: Doolittle's method supports row pivoting. Choleski's method does not support row pivoting.
    """
    def __init__(self, a, b, method="doolittle", tol=1.0e-12, pivot_on=False, dtype=np.float64):
        super().__init__(a, b, tol=tol, pivot_on=pivot_on, dtype=dtype)
        self._l = None
        self._u = None
        self._y = np.empty(self._b.shape, dtype=dtype)
        self._decomposed = False
        self._method = method.lower()

    def _doolittle_decompose(self):
        n = len(self._a)
        for k in range(n-1):
            if self._pivot_on: self._row_pivot(k)
            for i in range(k+1, n):
                if self._a[i, k] != 0.0:
                    lambda_ = self._a[i, k] / self._a[k, k]
                    self._a[i, k + 1:n] -= lambda_ * self._a[k, k + 1:n]
                    self._a[i, k] = lambda_
        self._check_with_tolerance(self._a[n - 1, n - 1])
        self._u = np.triu(self._a)
        self._l = np.identity(n) + np.tril(self._a, k=-1)
        self._decomposed = True

    def _choleski_decompose(self):
        n = len(self._a)
        for k in range(n):
            try:
                self._a[k, k] = np.sqrt(self._a[k, k] - np.dot(self._a[k, :k], self._a[k, :k]))
            except ValueError:
                raise ValueError("matrix is not positive definite")
            for i in range(k+1, n):
                self._a[i, k] = (self._a[i, k] - np.dot(self._a[i, :k], self._a[k, :k])) / self._a[k, k]
        self._l = np.tril(self._a)
        self._u = np.transpose(self._l)
        self._decomposed = True

    def _decompose(self):
        if self._method == "choleski":
            self._choleski_decompose()
        else:
            self._doolittle_decompose()

    def _forward_substitute(self):
        n = len(self._a)
        for k in range(n):
            self._y[k] = (self._b[k] - np.dot(self._l[k, :k], self._y[:k])) / self._l[k, k]

    def _backward_substitute(self):
        n = len(self._a)
        for k in range(n-1, -1, -1):
            self._x[k] = (self._y[k] - np.dot(self._u[k, k + 1:n], self._x[k + 1:n])) / self._u[k, k]

    def solve(self):
        if not self._solved:
            if not self._decomposed: self._decompose()
            self._forward_substitute()
            self._backward_substitute()
            self._solved = True
        return self._x.flatten()

    def solve_with_input(self, b):
        """Solve linear system with new input vector."""
        self._b = b
        if not self._decomposed: self._decompose()
        self._forward_substitute()
        self._backward_substitute()
        return self._x.flatten()

    @property
    def det(self):
        """
        Return determinant of coefficient matrix.
        Note: Only supported when using Doolittle's decomposition method, else returns None.
        """
        if self._method == "doolittle":
            if not self._decomposed: self._doolittle_decompose()
            if not self._det_a: self._det_a = self._determinant(self._u)
            return self._det_a

    @property
    def lowertri(self):
        """Return lower triangular matrix after LU-decomposition."""
        return self._l

    @property
    def uppertri(self):
        """Return upper triangular matrix after LU-decomposition."""
        return self._u


class _BandedLinSys:
    """Banded Linear System."""
    def __init__(self, c, d, e, b):
        self._c = np.array(c, dtype=np.float64, ndmin=2).T
        self._d = np.array(d, dtype=np.float64, ndmin=2).T
        self._e = np.array(e, dtype=np.float64, ndmin=2).T
        self._b = np.array(b, dtype=np.float64, ndmin=2).T
        self._y = np.empty(self._b.shape, dtype=np.float64)
        self._x = np.empty(self._b.shape, dtype=np.float64)
        self._solved = False

    def _decompose(self):
        pass

    def _forward_substitute(self):
        pass

    def _backward_substitute(self):
        pass

    def solve(self):
        """Solve banded linear system (banded tridiagonal or symmetric pentadiagonal coefficient matrix)."""
        if not self._solved:
            self._decompose()
            self._forward_substitute()
            self._backward_substitute()
            self._solved = True
        return self._x.flatten()


class B3DLinSys(_BandedLinSys):
    """Banded Tridiagonal Linear System."""
    def _decompose(self):
        n = len(self._d)
        for k in range(1, n):
            lambda_ = self._c[k-1] / self._d[k-1]
            self._d[k] -= lambda_ * self._e[k-1]
            self._c[k-1] = lambda_

    def _forward_substitute(self):
        n = len(self._d)
        self._y[0] = self._b[0]
        for k in range(1, n):
            self._y[k] = self._b[k] - self._c[k-1] * self._y[k-1]

    def _backward_substitute(self):
        n = len(self._d)
        self._x[n-1] = self._y[n-1] / self._d[n-1]
        for k in range(n-2, -1, -1):
            self._x[k] = (self._y[k] - self._e[k] * self._x[k+1]) / self._d[k]


class BS5DLinSys(_BandedLinSys):
    """Banded Symmetric Pentadiagonal Linear System."""
    def _decompose(self):
        n = len(self._d)
        for k in range(n-2):
            lambda_ = self._e[k] / self._d[k]
            self._d[k+1] -= lambda_ * self._e[k]
            self._e[k+1] -= lambda_ * self._c[k]
            self._e[k] = lambda_
            lambda_ = self._c[k] / self._d[k]
            self._d[k+2] -= lambda_ * self._c[k]
            self._c[k] = lambda_
        lambda_ = self._e[n-2] / self._d[n-2]
        self._d[n-1] -= lambda_ * self._e[n-2]
        self._e[n-2] = lambda_

    def _forward_substitute(self):
        n = len(self._d)
        self._y[0] = self._b[0]
        self._y[1] = self._b[1] - self._e[0] * self._y[0]
        for k in range(2, n):
            self._y[k] = self._b[k] - self._e[k-1] * self._y[k-1] - self._c[k-2] * self._y[k-2]

    def _backward_substitute(self):
        n = len(self._d)
        self._x[n-1] = self._y[n-1] / self._d[n-1]
        self._x[n-2] = self._y[n-2] / self._d[n-2] - self._e[n-2] * self._x[n-1]
        for k in range(n-3, -1, -1):
            self._x[k] = self._y[k] / self._d[k] - self._e[k] * self._x[k+1] - self._c[k] * self._x[k+2]
