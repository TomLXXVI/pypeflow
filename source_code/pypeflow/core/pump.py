"""
## Modeling a pump in a pipe section
"""
from typing import Tuple
import quantities as qty


class Pump:
    """
    Class for modeling a pump.
    A pump is modeled by a 2nd order polynomial. The coefficients can be derived from the pump curve in a data sheet.
    See also module pyflow.utils.pump_curve.
    """
    def __init__(self):
        self._a0: float = 0.0
        self._a1: float = 0.0
        self._a2: float = 0.0

    @classmethod
    def create(cls, a0: float, a1: float, a2: float):
        """
        Create configured Pump object passing the pump coefficients that describe the pump curve.
        The pump curve is expressed by the equation: dp = a0 + a1 * V + a2 * V **2

        **Parameters:**

        - `a0`: (*float*)
        - `a1`: (*float*)
        - `a2`: (*float*)

        """
        p = cls()
        p._a0 = a0
        p._a1 = a1
        p._a2 = a2
        return p

    def added_head(self, V: qty.VolumeFlowRate) -> qty.Pressure:
        """
        Calculate pump head (*quantities.Pressure*) that corresponds with given flow rate (*quantities.VolumeFlowRate*).

        """
        V = V()
        return qty.Pressure(self._a0 + self._a1 * V + self._a2 * V ** 2)

    @property
    def coefficients(self) -> Tuple[float, float, float]:
        """
        Get the pump coefficients (*Tuple[float, float, float]*) describing the pump curve.

        """
        return self._a0, self._a1, self._a2
