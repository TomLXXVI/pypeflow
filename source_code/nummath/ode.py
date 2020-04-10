import numpy as np


class ODESolver:
    """
    Solve ODE with fixed time step 'dt'. The ODE can be written like this:

        y^n = a[n-1] * y^(n-1) + a[n-2] * y^(n-2) + ... + a[1] * y^1 + a[0] * y + f_driver(t)

    This can be implemented as a function in Python:

        def f(t: float, y: List[float]) -> float:
            def f_driver(t):
                return <expression in variable t>
            return a[n-1] * y[n-1] + a[n-2] * y[n-2] + ... + a[1] * y[1] + a[0] * y[0] + f_driver(t)

    """
    def __init__(self, f, y0, dt, t_final=None, method='RK4', tol=1.0e-6):
        """
        Initialize ODE solver.
        Params:
            - f           name of function object
            - y0          list of initial values [y, y', y", ... y^(n-1)] at 't' = 0
            - dt          time step between successive solutions of y
            - t_final     time moment where the calculation may stop;
                          if None the ODE is solved for 1 time step -> use method 'step' instead of 'solve'
            - method      solving method
                          'RK4'     Runge-Kutta method of order 4 (default)
                          'RK2'     Runge-Kutta method of order 2 (aka modified Euler method using the midpoint rule)
                          'RK1'     Runge-Kutta method of order 1 (aka forward Euler method)
                          'BS'      Simplified Bulirsch-Stoer method with error control
        """
        self.f = f
        self.dt = dt
        self.y = np.array(y0)
        if t_final is not None:
            n = int(np.ceil(t_final / dt))
            self.t = np.array([k * dt for k in range(n + 1)])
            self.Y = np.empty((len(self.t), len(self.y)))
            self.Y[0, :] = self.y
        else:
            self.t = None
            self.Y = None
        self.tol = tol
        self._method = None
        method = method.upper()
        if method == 'RK1':
            self._method = self._RK1
        elif method == 'RK2':
            self._method = self._RK2
        elif method == 'RK4':
            self._method = self._RK4
        elif method == 'BS':
            self._method = self._BS
        else:
            raise ValueError(f"solving method {method} not implemented")

    def _F(self, t, y):
        if len(y) > 1:
            y_ = y[1:]
            y_f = np.array([self.f(t, y)])
            y = np.concatenate((y_, y_f))
        else:
            y = np.array([self.f(t, y)])
        return y

    def _RK1(self, t):
        """
        Runge-Kutta method of order 1 (forward Euler method).
        Solve (integrate) ODE over 1 time step 't + dt'.
        """
        K0 = self.dt * self._F(t, self.y)
        self.y = self.y + K0
        return self.y

    def _RK2(self, t):
        """
        Runge-Kutta method of order 2 (modified Euler method).
        Solve (integrate) ODE over 1 time step 't + dt'.
        """
        K0 = self.dt * self._F(t, self.y)
        K1 = self.dt * self._F(t + self.dt / 2.0, self.y + K0 / 2.0)
        self.y = self.y + K1
        return self.y

    def _RK4(self, t):
        """
        Runge-Kutta method of order 4.
        Solve (integrate) ODE over 1 time step 't + dt'.
        """
        K0 = self.dt * self._F(t, self.y)
        K1 = self.dt * self._F(t + self.dt / 2.0, self.y + K0 / 2.0)
        K2 = self.dt * self._F(t + self.dt / 2.0, self.y + K1 / 2.0)
        K3 = self.dt * self._F(t + self.dt, self.y + K2)
        self.y = self.y + (K0 + 2.0 * K1 + 2.0 * K2 + K3) / 6.0
        return self.y

    def __midpoint(self, t, no_steps):
        """
        Basic midpoint method.
        """
        dt = self.dt / no_steps
        y0 = self.y
        y1 = y0 + dt * self._F(t, y0)
        y2 = None
        for i in range(no_steps - 1):
            t = t + dt
            y2 = y0 + 2.0 * dt * self._F(t, y1)
            y0 = y1
            y1 = y2
        return 0.5 * (y1 + y0 + dt * self._F(t, y2))

    @staticmethod
    def __richardson(r, k):
        """
        Richardson extrapolation.
        """
        for j in range(k - 1, 0, -1):
            const = (k / (k - 1.0)) ** (2.0 * (k - j))
            r[j] = (const * r[j + 1] - r[j]) / (const - 1.0)
        return

    def _BS(self, t):
        """
        Combination of midpoint method and Richardson extrapolation.
        Solve (integrate) ODE over 1 time step 't + dt'.
        """
        k_max = 51
        n = len(self.y)
        r = np.zeros((k_max, n))
        no_steps = 2
        r[1] = self.__midpoint(t, no_steps)
        r_old = r[1].copy()
        for k in range(2, k_max):
            no_steps = 2 * k
            r[k] = self.__midpoint(t, no_steps)
            self.__richardson(r, k)
            e = np.sqrt(np.sum((r[1] - r_old) ** 2) / n)
            if e < self.tol:
                self.y = r[1]
                return self.y
            r_old = r[1].copy()
        raise OverflowError('midpoint method did not converge')

    def solve(self):
        """
        Solve ODE from 't' = 0 to 't_final'.
        """
        for k in range(1, len(self.t)):
            self.Y[k, :] = self._method(self.t[k - 1])
        return self.t, self.Y

    def step(self, t):
        """
        Solve ODE for the next time step.
        """
        return self._method(t)


class AdaptiveODESolver:
    """Solve ODE with variable time step for error control."""
    def __init__(self, f, y0, t_final, dt_init, tol=1.0e6):
        """
        Initialize ODE solver.
        Params:
            - f           name of function object with signature f(t, [y, y', y", ... y^(n-1)])
            - y0          list of initial values [y, y', y", ... y^(n-1)] at 't' = 0
            - dt          initial time step between successive solutions of y
            - t_final     time moment where the calculation may stop.
            - tol         error tolerance for the per-step error
        """
        self.f = f
        self.dt = dt_init
        self.y = np.array(y0)
        self.t_final = t_final
        self.tol = tol
        self.t = [0.0]
        self.Y = [self.y]
        self.stop = False

    def _F(self, t, y):
        y_ = y[1:]
        y_f = np.array([self.f(t, y)])
        return np.concatenate((y_, y_f))

    def _RK5(self):
        """
        Adaptive Runge-Kutta method of order 5.
        """
        t = 0.0  # calculation starts at 't' = 0.

        a1 = 0.2
        a2 = 0.3
        a3 = 0.8
        a4 = 8 / 9
        a5 = 1.0
        a6 = 1.0
        c0 = 35 / 384
        c2 = 500 / 1113
        c3 = 125 / 192
        c4 = -2187 / 6784
        c5 = 11 / 84
        d0 = 5179 / 57600
        d2 = 7571 / 16695
        d3 = 393 / 640
        d4 = -92097 / 339200
        d5 = 187 / 2100
        d6 = 1 / 40
        b10 = 0.2
        b20 = 0.075
        b21 = 0.225
        b30 = 44 / 45
        b31 = -56 / 15
        b32 = 32 / 9
        b40 = 19372 / 6561
        b41 = -25360 / 2187
        b42 = 64448 / 6561
        b43 = -212 / 729
        b50 = 9017 / 3168
        b51 = -355 / 33
        b52 = 46732 / 5247
        b53 = 49 / 176
        b54 = -5103 / 18656
        b60 = 35 / 384
        b62 = 500 / 1113
        b63 = 125 / 192
        b64 = -2187 / 6784
        b65 = 11 / 84

        K0 = self.dt * self._F(t, self.y)

        for i in range(500):
            K1 = self.dt * self._F(t + a1 * self.dt, self.y + b10 * K0)
            K2 = self.dt * self._F(t + a2 * self.dt, self.y + b20 * K0 + b21 * K1)
            K3 = self.dt * self._F(t + a3 * self.dt, self.y + b30 * K0 + b31 * K1 + b32 * K2)
            K4 = self.dt * self._F(t + a4 * self.dt, self.y + b40 * K0 + b41 * K1 + b42 * K2 + b43 * K3)
            K5 = self.dt * self._F(t + a5 * self.dt, self.y + b50 * K0 + b51 * K1 + b52 * K2 + b53 * K3 + b54 * K4)
            K6 = self.dt * self._F(t + a6 * self.dt, self.y + b60 * K0 + b62 * K2 + b63 * K3 + b64 * K4 + b65 * K5)

            dy = c0 * K0 + c2 * K2 + c3 * K3 + c4 * K4 + c5 * K5
            # truncation error vector representing the errors in the variables [y, y',..]
            E = (c0 - d0) * K0 + (c2 - d2) * K2 + (c3 - d3) * K3 + (c4 - d4) * K4 + (c5 - d5) * K5 - d6 * K6
            # error measure = root mean square of error vector 'E'
            e = np.sqrt(np.sum(E ** 2) / len(self.y))
            dt_next = 0.9 * self.dt * (self.tol / e) ** 0.2
            if e <= self.tol:  # if error within tolerance
                self.y = self.y + dy  # accept solution
                t = t + self.dt
                self.t.append(t)
                self.Y.append(self.y)
                if self.stop:
                    break
                if abs(dt_next) > 10.0 * abs(self.dt):
                    dt_next = 10.0 * self.dt
                # check if next step is the last one; if so, adjust time step
                if (self.dt > 0.0) == ((t + dt_next) >= self.t_final):
                    dt_next = self.t_final - t
                    self.stop = True
                K0 = K6 * dt_next / self.dt
            else:  # if error outside tolerance, scrap the current step and repeat with 'dt_next'
                if abs(dt_next) < 0.1 * abs(self.dt):
                    dt_next = 0.1 * self.dt
                K0 = K0 * dt_next / self.dt
            self.dt = dt_next

    def solve(self):
        """
        Solve ODE with adaptive Runge-Kutta method of order 5.
        """
        self._RK5()
        return np.array(self.t), np.array(self.Y)


def ode_print(t, Y, freq=1):
    """
    Print the solutions of an ODE in columns ( t   y   y'  ... y^(n-1)   )
    Params:
        - t     array with 't' values
        - Y     matrix with 'y' values [y, y', y",..., y^(n-1)] at each 't'
        - freq  the step between lines
    """

    def print_heading(n):
        print("t".center(13), end=" ")
        for i in range(n):
            print(f"y[{i}]".center(13), end=" ")
        print()

    def print_line(t_, y, n):
        print(f"{t_:.4f}".rjust(13), end=" ")
        for i in range(n):
            print(f"{y[i]:.4f}".rjust(13), end=" ")
        print()

    row_num = Y.shape[0]
    col_num = Y.shape[1]

    print_heading(col_num)

    for k in range(0, row_num, freq):
        print_line(t[k], Y[k, :], col_num)


if __name__ == '__main__':

    from nummath.graphing2 import LineGraph

    def f(t, y):
        return -0.1 * y[1] + 0.0 * y[0] - t


    ode_solver = ODESolver(f=f, y0=[0, 1], dt=0.05, t_final=2.0)
    t, y = ode_solver.solve()

    g = LineGraph(fig_size=(8, 8), dpi=96)
    g.add_dataset(name='ode', x1_data=t, y1_data=y[:, 0])
    g.show()
