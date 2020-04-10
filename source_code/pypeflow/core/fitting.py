"""
## Modeling a fitting or valve in a pipe section
"""

from typing import Optional, Dict
import math
import quantities as qty
from pypeflow.core.fluids import Fluid
from pypeflow.core.resistance_coefficient import ResistanceCoefficient


class Fitting:
    """Class that models a fitting or valve in a pipe section."""

    def __init__(self):
        self._type: str = ''
        self._fluid: Optional[Fluid] = None
        self._flow_rate: float = math.nan
        self._vel: float = math.nan
        self._di: float = math.nan
        self._Kv: float = math.nan
        self._zeta: float = math.nan
        self._zeta_inf: float = math.nan
        self._zeta_d: float = math.nan
        self._ELR: float = math.nan
        self._dp: float = math.nan

    @classmethod
    def create_w_flow_rate(cls, type_: str, fluid: Fluid, flow_rate: qty.VolumeFlowRate, Kv: float):
        """
        Create a Fitting object if the flow rate in the pipe section and flow coefficient of the fitting or valve
        are known.

        **Parameters:**

        - `type_` : (*str*) = description of the type of fitting/valve (free to choose).
        - `fluid` : (*core.fluids.Fluid*) = fluid that flows through the fitting/valve.
        - `flow_rate` : (*quantities.VolumeFlowRate*) = flow rate through fitting/valve.
        - `Kv` : (*float*) =  flow coefficient of the fitting/valve [bar/(m^3/h)^2]

        """
        f = cls()
        f.type = type_
        f.fluid = fluid
        f.flow_rate = flow_rate
        f.set_coefficients(Kv=Kv)
        return f

    @classmethod
    def create_w_velocity(cls, type_: str, fluid: Fluid, velocity: qty.Velocity,
                          di: Optional[qty.Length], **coefficients):
        """
        Create a Fitting object if the flow velocity in the pipe section and resistance coefficient of the fitting or
        valve are known.

        **Parameters:**

        - `type_` : (*str*) = description of the type of fitting/valve (free to choose)
        - `fluid` : (*core.fluids.Fluid*) = fluid that flows through the fitting or valve
        - `velocity` : (*quantities.Velocity*) = flow velocity in the pipe section
        - `di` : (*quantities.Length*) = inside diameter of the pipe section
        - coefficients: keyword arguments = possible parameters expressing the resistance coefficient of the
        fitting/valve:

            + `zeta` : *float*
            + `zeta_inf` : *float*
            + `zeta_d` : *float*
            + `ELR` : *float*

        """
        f = cls()
        f.type = type_
        f.fluid = fluid
        f.velocity = velocity
        f.diameter = di
        f.set_coefficients(**coefficients)
        return f

    def _calc_pressure_drop(self):
        """Calculate pressure drop across fitting or valve."""
        if not math.isnan(self._Kv):
            self._dp = self._calc_pressure_drop_Kv()
        elif not math.isnan(self._zeta_inf):
            self._dp = self._calc_pressure_drop_3K()
        elif not math.isnan(self._ELR):
            self._dp = self._calc_pressure_drop_ELR()
        elif not math.isnan(self._zeta):
            self._dp = self._calc_pressure_drop_1K()

    def _calc_pressure_drop_Kv(self) -> float:
        """Calculate pressure drop across valve with given flow coefficient Kv."""
        rho_15 = 999.0  # water density @ 15 °C
        Av = self._Kv * math.sqrt(rho_15) / (3.6e5 * math.sqrt(10))
        return self._fluid.density('kg/m^3') * (self._flow_rate / Av) ** 2

    def _calc_pressure_drop_1K(self) -> float:
        """Calculate pressure drop across fitting with given resistance coefficient."""
        vp = self._fluid.density('kg/m^3') * self._vel ** 2.0 / 2.0
        return self._zeta * vp

    def _calc_pressure_drop_3K(self) -> float:
        """Calculate pressure drop across fitting with 3K-method."""
        vp = self._fluid.density('kg/m^3') * self._vel ** 2.0 / 2.0
        re = self._vel * self._di / self._fluid.kinematic_viscosity('m^2/s')
        return ((self._zeta / re) + self._zeta_inf * (1 + self._zeta_d / self._di ** 0.3)) * vp

    def _calc_pressure_drop_ELR(self) -> float:
        """Calculate pressure drop across fitting with Crane-K-method."""
        vp = self._fluid.density('kg/m^3') * self._vel ** 2.0 / 2.0
        zeta = ResistanceCoefficient.from_ELR(self._ELR, qty.Length(self._di))
        return zeta * vp

    @property
    def pressure_drop(self) -> qty.Pressure:
        """
        Get the pressure drop (*quantities.Pressure*) across the fitting or valve.

        """
        self._calc_pressure_drop()
        return qty.Pressure(self._dp)

    @property
    def zeta(self) -> float:
        """
        Get the resistance coefficient (*float*) of the fitting or valve.

        """
        if not math.isnan(self._zeta_inf):
            dp = self._calc_pressure_drop_3K()
            vp = self._fluid.density('kg/m^3') * self._vel ** 2.0 / 2.0
            return dp / vp
        elif not math.isnan(self._zeta):
            return self._zeta
        elif not math.isnan(self._Kv):
            return ResistanceCoefficient.from_Kv(self._Kv, qty.Length(self._di))
        elif not math.isnan(self._ELR):
            return ResistanceCoefficient.from_ELR(self._ELR, qty.Length(self._di))

    @property
    def flow_rate(self) -> qty.VolumeFlowRate:
        """
        Get/set the flow rate (*quantities.VolumeFlowRate*) through the fitting or valve.

        """
        return qty.VolumeFlowRate(self._flow_rate)

    @flow_rate.setter
    def flow_rate(self, V: qty.VolumeFlowRate):
        self._flow_rate = V()

    @property
    def velocity(self) -> qty.Velocity:
        """
        Get/set the flow velocity (*quantities.Velocity*) in the pipe section of the fitting or valve.

        """
        return qty.Velocity(self._vel)

    @velocity.setter
    def velocity(self, v: qty.Velocity):
        self._vel = v()

    @property
    def fluid(self) -> Fluid:
        """
        Get/set the fluid (object of type *core.fluids.Fluid*) through the fitting or valve.

        """
        return self._fluid

    @fluid.setter
    def fluid(self, fl: Fluid):
        self._fluid = fl

    @property
    def diameter(self) -> qty.Length:
        """
        Get/set the inside diameter (object of type *quantities.Length*) of the pipe section the fitting or valve
        belongs to.

        """
        return qty.Length(self._di)

    @diameter.setter
    def diameter(self, di: qty.Length):
        self._di = di()

    @property
    def type(self) -> str:
        """
        Get/set a description (*str*) for the kind of fitting or valve.

        """
        return self._type

    @type.setter
    def type(self, t: str):
        self._type = t

    def set_coefficients(self, **kwargs):
        """
        Set the resistance coefficient of the fitting or valve. Different parameters are possible to express or to
        derive the resistance coefficient of fittings and valves.

        **kwargs:**

        - `Kv`: (*float*) = flow coefficient [bar/(m^3/h)^2]
        - `zeta`: (*float*) = resistance coefficient
        - `zeta_inf`: (*float*) = resistance coefficient (see 3K-method)
        - `zeta_d`: (*float*) = resistance coefficient (see 3K-method)
        - `ELR`: (*float*) = equivalent Length Ratio (see Crane-K-method)

        """
        self._Kv = kwargs.get('Kv', math.nan)
        self._zeta = kwargs.get('zeta', math.nan)
        self._zeta_inf = kwargs.get('zeta_inf', math.nan)
        self._zeta_d = kwargs.get('zeta_d', math.nan)
        self._ELR = kwargs.get('ELR', math.nan)

    def get_coefficients(self) -> Dict[str, float]:
        """
        Get the resistance coefficient(s) of the fitting or valve.

        **Returns:** (*Dict[str, float]*)<br>
        Keys:

        + 'zeta'
        + 'zeta_inf'
        + 'zeta_d'
        + 'ELR'
        + 'Kv'

        """
        return {
            'zeta': self._zeta,
            'zeta_inf': self._zeta_inf,
            'zeta_d': self._zeta_d,
            'ELR': self._ELR,
            'Kv': self._Kv
        }
