"""
## Convert flow coefficients of fittings and valves
"""
import math
import quantities as qty
from pypeflow.core.fluids import Water


class FlowCoefficient:
    """Class that groups class methods to convert between flow coefficient units."""

    rho: float = Water(15).density('kg/m^3')  # water density @ 15 °C

    @classmethod
    def Av_to_Kv(cls, Av: float) -> float:
        """
        Convert Av value (flow rate in m^3/s and pressure in Pa) (*float*) to Kv value (flow rate in m^3/h, pressure in
        bar and with density of water at 15 °C) (*float*).

        """
        Kv = Av * 3.6e5 * math.sqrt(10) / math.sqrt(cls.rho)
        return Kv

    @classmethod
    def Kv_to_Av(cls, Kv: float) -> float:
        """
        Convert Kv (*float*) to Av value (*float*).

        """
        Av = Kv * math.sqrt(cls.rho) / (3.6e5 * math.sqrt(10))
        return Av

    @classmethod
    def calc_Kv(cls, V: qty.VolumeFlowRate, dp: qty.Pressure) -> float:
        """
        Calculate flow coefficient Kv (*float*) of a piping element if flow rate (*quantities.VolumeFlowRate*) and
        pressure drop (*quantities.Pressure*) are known.

        """
        V_base = V('m^3/h')
        dp_base = dp('bar')
        Kv = V_base / math.sqrt(dp_base)
        return Kv
