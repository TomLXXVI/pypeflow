"""
## Calculate resistance coefficients of fittings/valves
"""

from typing import Tuple
import math
from pypeflow.core.pipe_schedules import PipeSchedule40
from pypeflow.core.flow_coefficient import FlowCoefficient
import quantities as qty


class ResistanceCoefficient:
    """
    Base class that groups some static methods to convert a flow coefficient or equivalent length ratio (ELR) into
    a corresponding resistance coefficient.
    """

    @staticmethod
    def from_Kv(Kv: float, di: qty.Length) -> float:
        """Calculate resistance coefficient of fitting from Kv flow coefficient.

        **Parameters:**

        - `Kv`: (*float*) = flow coefficient of fitting/valve [flow rate m^3/h, pressure drop bar]
        - `di`: (*qty.Length*) = referenced internal pipe diameter

        **Returns:** (*float*)

        """
        Av = FlowCoefficient.Kv_to_Av(Kv)
        zeta = math.pi ** 2 * di('m') ** 4 / (8.0 * Av ** 2)
        return zeta

    @staticmethod
    def from_Av(Av: float, di: qty.Length) -> float:
        """Calculate the resistance coefficient of fitting/valve from its flow coefficient Av.

        **Parameters:**

        - `Av`: (*float*) = flow coefficient of fitting/valve [flow rate m^3/s, pressure drop Pa]
        - `di`: (*qty.Length*) = referenced internal pipe diameter

        **Returns:** (*float*)

        """
        zeta = math.pi ** 2 * di('m') ** 4 / (8.0 * Av ** 2)
        return zeta

    @staticmethod
    def from_ELR(ELR: float, di: qty.Length) -> float:
        """Calculate resistance coefficient of fitting/valve from equivalent length ratio ELR (see Crane-K-method).

        **Parameters:**

        - `ELR`: (*float*) = equivalent length ratio (Le/di) of fitting/valve.
        - `di`: (*qty.Length*) = referenced internal pipe diameter.

        **Returns:** (*float*)

        """
        dn = PipeSchedule40.nominal_diameter(d_int=di)
        di_40 = PipeSchedule40.inside_diameter(dn)
        # pipe roughness for schedule 40 [mm]
        eps = PipeSchedule40.pipe_roughness('mm')
        # friction factor for completely turbulent flow
        f = 0.25 / (math.log10(eps / (3.7 * di_40('mm')))) ** 2
        zeta = f * ELR * (di('mm') / di_40('mm')) ** 4.0
        return zeta


class Tee(ResistanceCoefficient):
    """Calculate resistance coefficient of a Tee or Wye."""

    def __init__(self, **kwargs):
        """
        **kwargs:**

        - `flow_pattern`: (*str*) = possible values: 'diverging'/'converging'
        - `d_branch`: (*float*) = branch leg diameter [mm]
        - `d_combined`: (*float*) = combined leg diameter [mm]
        - `flow_rate_branch`: (*float*) = flow rate in branch leg [m^3/s]
        - `flow_rate_combined`: (*float*) = flow rate in combined leg [m^3/s]
        - `theta`: (*float*) = branch leg angle [deg]

        """
        self._flow_pattern: str = kwargs.get('flow_pattern')
        self._d_branch: float = kwargs.get('d_branch')  # mm
        self._d_combined: float = kwargs.get('d_combined')  # mm
        self._flow_rate_branch: float = kwargs.get('flow_rate_branch')  # m^3/s
        self._flow_rate_combined: float = kwargs.get('flow_rate_combined')  # m^3/s
        self._theta: float = kwargs.get('theta', 90.0)  # deg

        self._zeta_run: float = 0.0
        self._zeta_branch: float = 0.0
        if self._flow_pattern == 'converging':
            self._zeta_run, self._zeta_branch = self._tee_converging()
        if self._flow_pattern == 'diverging':
            self._zeta_run, self._zeta_branch = self._tee_diverging()

    def _tee_converging(self) -> Tuple[float, float]:
        """Calculate resistance coefficient of straight leg and branch leg of a converging tee or wye."""
        beta = (self._d_branch / self._d_combined) ** 2
        V_rat = self._flow_rate_branch / self._flow_rate_combined
        cb = self._calc_c_branch(beta, V_rat)
        db, eb, fb, cr, dr, er, fr = self._get_coefficients(self._theta)
        zeta_branch = cb * (1.0 + db * (V_rat * 1.0 / beta) ** 2
                            - eb * (1.0 - V_rat) ** 2 - fb * 1.0 / beta * V_rat ** 2)
        if self._theta == 90.0:
            zeta_run = 1.55 * V_rat - V_rat ** 2
        else:
            zeta_run = cr * (1.0 + dr * (V_rat * 1.0 / beta) ** 2 - er * (1.0 - V_rat) ** 2
                             - fr * 1.0 / beta * V_rat ** 2)
        # zeta_branch and zeta_run are both referenced to the pipe section velocity in the combined leg, but
        # we want zeta_branch to be referenced to the pipe section velocity in the branch leg, therefore:
        zeta_branch = zeta_branch * beta * (1.0 / V_rat) ** 2
        return zeta_run, zeta_branch

    @staticmethod
    def _calc_c_branch(beta: float, V_rat: float) -> float:
        cb = math.nan
        if beta <= 0.35:
            cb = 1.0
        elif beta > 0.35:
            if V_rat <= 0.4:
                cb = 0.9 * (1.0 - V_rat)
            elif V_rat > 0.4:
                cb = 0.55
        return cb

    @staticmethod
    def _get_coefficients(theta: float) -> Tuple[float, ...]:
        data = {
            30.0: [1.0, 2.0, 1.74, 1.0, 0.0, 1.0, 1.74],
            45.0: [1.0, 2.0, 1.41, 1.0, 0.0, 1.0, 1.41],
            60.0: [1.0, 2.0, 1.0, 1.0, 0.0, 1.0, 1.0],
            90.0: [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        }
        return tuple(data[theta])

    def _tee_diverging(self) -> Tuple[float, float]:
        """Calculate resistance coefficient of straight leg and branch leg of a diverging tee or wye."""
        beta = (self._d_branch / self._d_combined) ** 2
        V_rat = self._flow_rate_branch / self._flow_rate_combined
        g = h = j = 0.0
        if 0.0 < self._theta <= 60.0:
            if beta <= 0.35:
                if V_rat <= 0.4:
                    g = 1.1 - 0.7 * V_rat
                elif V_rat > 0.4:
                    g = 0.85
            elif beta > 0.35:
                if V_rat <= 0.6:
                    g = 1.0 - 0.6 * V_rat
                elif V_rat > 0.6:
                    g = 0.6
            h = 1.0
            j = 2.0
        elif self._theta == 90.0:
            if math.sqrt(beta) <= 2.0 / 3.0:
                g = 1.0
                h = 1.0
                j = 2.0
            elif beta == 1.0 or V_rat * 1.0 / beta <= 2.0:
                g = 1.0 + 0.3 * V_rat ** 2
                h = 0.3
                j = 0.0
        zeta_branch = g * (1.0 + h * (V_rat * 1.0 / beta) ** 2
                           - j * (V_rat * 1.0 / beta) * math.cos(math.radians(self._theta)))
        m = 0.0
        if beta <= 0.4:
            m = 0.4
        elif beta > 0.4:
            if V_rat <= 0.5:
                m = 2.0 * (2.0 * V_rat - 1.0)
            elif V_rat > 0.5:
                m = 0.3 * (2.0 * V_rat - 1.0)
        zeta_run = m * V_rat ** 2
        # zeta_branch and zeta_run are both referenced to the pipe section velocity in the combined leg
        # we want zeta_branch to be referenced to the pipe section velocity in the branch leg, therefore:
        zeta_branch = zeta_branch * beta * (1.0 / V_rat) ** 2
        return zeta_run, zeta_branch

    @property
    def zeta_branch(self) -> float:
        """Get resistance coefficient (*float*) of branch leg."""
        return self._zeta_branch

    @property
    def zeta_run(self) -> float:
        """Get resistance coefficient (*float*) of run or straight leg."""
        return self._zeta_run


class Reducer(ResistanceCoefficient):
    """Calculate resistance coefficient of a reducer."""

    def __init__(self, **kwargs):
        """
        **kwargs:**

        - `d_large`: (*float*) = diameter of large side [mm]
        - `d_small`: (*float*) = diameter of small side [mm]
        - `length`: (*float*) = length of reducer [mm]

        """
        self._d_large: float = kwargs.get('d_large')  # mm
        self._d_small: float = kwargs.get('d_small')  # mm
        self._length: float = kwargs.get('length')    # mm

        self._zeta_small, self._zeta_large = self._reducer()

    def _reducer(self) -> Tuple[float, float]:
        beta = self._d_small / self._d_large
        theta = 2.0 * math.atan((self._d_large - self._d_small) / (2.0 * self._length))
        zeta_small = math.nan
        zeta_large = math.nan
        if theta <= math.pi / 4.0:
            zeta_small = 0.8 * math.sin(theta / 2.0) * (1 - beta ** 2)
            zeta_large = zeta_small / beta ** 4
        elif math.pi / 4.0 < theta <= math.pi:
            zeta_small = 0.5 * math.sqrt(math.sin(theta / 2.0)) * (1 - beta ** 2)
            zeta_large = zeta_small / beta ** 4
        return zeta_small, zeta_large

    @property
    def zeta_small(self) -> float:
        """Get resistance coefficient (*float*) of small side of reducer."""
        return self._zeta_small

    @property
    def zeta_large(self):
        """Get resistance coefficient (*float*) of large side of reducer."""
        return self._zeta_large


class Enlarger(ResistanceCoefficient):
    """Resistance coefficient of an Enlarger."""

    def __init__(self, **kwargs):
        """
        **kwargs:**

        - `d_large`: (*float*) = diameter of large side [mm]
        - `d_small`: (*float*) = diameter of small side [mm]
        - `length`: (*float*) = length of enlarger [mm]

        """
        self._d_large: float = kwargs.get('d_large')  # mm
        self._d_small: float = kwargs.get('d_small')  # mm
        self._length: float = kwargs.get('length')    # mm

        self._zeta_small, self._zeta_large = self._enlarger()

    def _enlarger(self) -> Tuple[float, float]:
        beta = self._d_small / self._d_large
        theta = 2 * math.atan((self._d_large - self._d_small) / (2 * self._length))
        zeta_small = math.nan
        zeta_large = math.nan
        if theta <= math.pi / 4.0:
            zeta_small = 2.6 * math.sin(theta / 2) * (1 - beta ** 2) ** 2
            zeta_large = zeta_small / beta ** 4
        elif math.pi / 4.0 < theta <= math.pi:
            zeta_small = (1 - beta ** 2) ** 2
            zeta_large = zeta_small / beta ** 4
        return zeta_small, zeta_large

    @property
    def zeta_small(self) -> float:
        """Get resistance coefficient (*float*) referred to small side of enlarger."""
        return self._zeta_small

    @property
    def zeta_large(self) -> float:
        """Get resistance coefficient (*float*) referred to large side of enlarger."""
        return self._zeta_large


class ValveReducedPortType1(ResistanceCoefficient):
    """
    Resistance coefficient of a Reduced Port Valve Type 1:

    - gate valve
    - ball valve

    """

    def __init__(self, **kwargs):
        """
        **kwargs:**

        - `d_large`: (*float*) = diameter of large side [mm]
        - `d_small`: (*float*) = diameter of small side [mm]
        - `reduction_angle`: (*float*) = angle of port reduction [deg]
        - `zeta_unreduced`: (*float*) = resistance coefficient without reduced port.

        """
        self._d_small: float = kwargs.get('d_small')  # mm
        self._d_large: float = kwargs.get('d_large')  # mm
        self._theta: float = kwargs.get('reduction_angle')  # deg
        self._zeta_unreduced: float = kwargs.get('zeta_unreduced')  # resistance_coefficient without reduced port

        self._zeta = self._valve_reduced_port_type1()

    def _valve_reduced_port_type1(self) -> float:
        beta = self._d_small / self._d_large
        zeta_reduced = math.nan
        theta = math.radians(self._theta)
        if beta < 1.0 and theta <= math.pi / 4.0:
            zeta_reduced = ((self._zeta_unreduced + math.sin(theta / 2.0)
                             * (0.8 * (1.0 - beta ** 2) + 2.6 * (1.0 - beta ** 2) ** 2)) / beta ** 4)
        elif beta < 1.0 and math.pi / 4.0 < theta <= math.pi:
            zeta_reduced = ((self._zeta_unreduced + 0.5 * math.sqrt(math.sin(theta / 2.0)) * (1.0 - beta ** 2)
                             + (1.0 - beta ** 2) ** 2) / beta ** 4)
        return zeta_reduced

    @property
    def zeta(self) -> float:
        """Get the resistance coefficient (*float*) of the reduced port valve."""
        return self._zeta


class GateValveReducedPort(ValveReducedPortType1):
    """Derived class of ValveReducedPortType1."""
    pass


class BallValveReducedPort(ValveReducedPortType1):
    """Derived class of ValveReducedPortType1."""
    pass


class ValveReducedPortType2(ResistanceCoefficient):
    """
    Resistance coefficient of a Reduced Port Valve Type 2:

    - globe valve
    - angle valve
    - check valve of lift type
    - check valve of stop type
    - plug valve
    - cock

    """

    def __init__(self, **kwargs):
        """
        **kwargs:**

        - `d_large`: (*float*) = diameter of large side [mm]
        - `d_small`: (*float*) = diameter of small side [mm]
        - `zeta_unreduced`: (*float*) = resistance coefficient without reduced ports.

        """

        self._d_small = kwargs.get('d_small')  # mm
        self._d_large = kwargs.get('d_large')  # mm
        self._zeta_unreduced = kwargs.get('zeta_unreduced')  # resistance_coefficient without reduced port

        self._zeta = self._valve_reduced_port_type2()

    def _valve_reduced_port_type2(self) -> float:
        beta = self._d_small / self._d_large
        zeta_reduced = (self._zeta_unreduced + beta * (0.5 * (1.0 - beta ** 2) + (1.0 - beta ** 2) ** 2)) / beta ** 4
        return zeta_reduced

    @property
    def zeta(self):
        """Get resistance coefficient of reduced port valve."""
        return self._zeta


class GlobeValveReducedPort(ValveReducedPortType2):
    pass


class AngleValveReducedPort(ValveReducedPortType2):
    pass


class LiftCheckValveReducedPort(ValveReducedPortType2):
    pass


class StopCheckValveReducedPort(ValveReducedPortType2):
    pass


class PlugValveReducedPort(ValveReducedPortType2):
    pass


class CockReducedPort(ValveReducedPortType2):
    pass
