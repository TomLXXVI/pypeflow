"""
## Modeling straight pipe
"""
from typing import Optional, Type
import math
import quantities as qty
from pypeflow.core.fluids import Fluid
from pypeflow.core.pipe_schedules import PipeSchedule
from pypeflow.core.cross_sections import Circular


def reynolds_number(v: float, d_hyd: float, kin_visco: float) -> float:
    """
    Calculate Reynolds number.

    **Parameters:**

    - `v`: (*float*) = flow velocity [m/s]
    - `d_hyd`: (*float*) = hydraulic diameter [m]
    - `kin_visco`: (*float*) = kinematic viscosity [m^2/s]

    **Returns:** (*float*)

    """
    return v * d_hyd / kin_visco


def _haaland(re: float, rel_pipe_rough: float) -> float:
    # Haaland equation for calculating the Darcy friction factor.
    var = 6.9 / re + (rel_pipe_rough / 3.71) ** 1.11
    return (1.0 / (-1.8 * math.log10(var))) ** 2.0


def _serghide(re: float, rel_pipe_rough: float) -> float:
    # Serghide equation for calculating the Darcy friction factor.
    var1 = -2.0 * math.log10(rel_pipe_rough / 3.7 + 12.0 / re)
    var2 = -2.0 * math.log10(rel_pipe_rough / 3.7 + 2.51 * var1 / re)
    var3 = -2.0 * math.log10(rel_pipe_rough / 3.7 + 2.51 * var2 / re)
    return (var1 - (var2 - var1) ** 2.0 / (var3 - 2.0 * var2 + var1)) ** -2.0


def darcy_friction_factor(re: float, rel_pipe_rough: float, use: str = 'haaland') -> float:
    """
    Calculate the Darcy friction factor.

    **Parameters:**

    - `re`: (*float*) = Reynolds number
    - `rel_pipe_rough`: (*float*) = relative pipe wall roughness
    - `use`: (*str*) = friction factor equation to be used. valid values: 'haaland'/'serghide'

    **Returns:** (*float*)

    """
    if use == 'serghide':
        return _serghide(re, rel_pipe_rough)
    else:
        return _haaland(re, rel_pipe_rough)


class Pipe:
    """Class that models straight pipe."""

    def __init__(self):
        self._length: float = math.nan
        self._fluid: Optional[Fluid] = None
        self._rough: float = math.nan
        self._flow_rate: float = math.nan
        self._dp_fric: float = math.nan
        self._dp_minor: float = math.nan
        self._cross_section: Circular = Circular()
        self._max_iterations: int = 30

    @classmethod
    def create(cls, fluid: Fluid, pipe_schedule: Type[PipeSchedule], length: qty.Length, **kwargs) -> 'Pipe':
        """
        Create a configured Pipe object.<br>

        - If flow rate and nominal diameter are given, the pressure loss in the pipe is calculated.
        - If flow rate and friction loss are given, the diameter of the pipe is calculated.
        - If friction loss and nominal diameter are given, the flow rate is calculated.

        **Parameters:**

        - `fluid`: (object of type *pyflow.core.fluids.Fluid*) = fluid that flow through the pipe
        - `pipe_schedule`: (type of *pyflow.core.pipe_schedules.PipeSchedule*) = pipe schedule
        - `length`: (*quantities.Length*) = the length of the pipe
        - `kwargs`: optional keyword arguments:
            + `flow_rate`: (*quantities.VolumeFlowRate*) = flow rate through the pipe
            + `nominal_diameter`: (*quantities.Length*) = the nominal diameter of the pipe
            + `friction_loss`: (*quantities.Pressure*) = the friction loss in the pipe
            + `sum_zeta`: (*float*) = sum of resistance coefficients of fittings/valves in the pipe

        **Returns:** (*Pipe* object)

        """
        p = cls()
        p.fluid = fluid
        p.length = length
        p.roughness = pipe_schedule.pipe_roughness
        V = kwargs.get('flow_rate')
        dpf = kwargs.get('friction_loss')
        dn = kwargs.get('nominal_diameter')
        sum_zeta = kwargs.get('sum_zeta', 0.0)
        if (V is not None) and (dpf is not None):
            p.cross_section = Circular.create(pipe_schedule)
            p.flow_rate = V
            p.friction_loss = dpf
            p.calculate_diameter()
        if (V is not None) and (dn is not None):
            p.cross_section = Circular.create(pipe_schedule, dn=dn)
            p.flow_rate = V
            p.calculate_pressure_loss(sum_zeta)
        if (dpf is not None) and (dn is not None):
            p.cross_section = Circular.create(pipe_schedule, dn=dn)
            p.friction_loss = dpf
            p.calculate_flow_rate(sum_zeta)
        return p

    @property
    def length(self) -> qty.Length:
        """Get/set the length (*quantities.Length*) of the pipe."""
        return qty.Length(self._length)

    @length.setter
    def length(self, l: qty.Length):
        self._length = l()

    @property
    def roughness(self) -> qty.Length:
        """Get/set the pipe wall roughness (*quantities.Length*) of the pipe."""
        return qty.Length(self._rough)

    @roughness.setter
    def roughness(self, r: qty.Length):
        self._rough = r()

    @property
    def flow_rate(self) -> qty.VolumeFlowRate:
        """Get/set the flow rate (*quantities.VolumeFlowRate*) through the pipe."""
        return qty.VolumeFlowRate(self._flow_rate)

    @flow_rate.setter
    def flow_rate(self, V: qty.VolumeFlowRate):
        self._flow_rate = V()

    @property
    def velocity(self) -> qty.Velocity:
        """Get the flow velocity (*quantities.Velocity*) in the pipe."""
        v = self._flow_rate / self._cross_section.area()
        return qty.Velocity(v)

    @property
    def velocity_pressure(self) -> qty.Pressure:
        """Get the velocity pressure (*quantities.Pressure*) in the pipe."""
        rho = self._fluid.density()
        v = self._flow_rate / self._cross_section.area()
        return qty.Pressure(rho * v ** 2.0 / 2.0)

    @property
    def friction_loss(self) -> qty.Pressure:
        """Get/set the friction loss (*quantities.Pressure*) across the pipe."""
        return qty.Pressure(self._dp_fric)

    @friction_loss.setter
    def friction_loss(self, dp_fric: qty.Pressure):
        self._dp_fric = dp_fric()

    @property
    def minor_losses(self) -> qty.Pressure:
        """Get the sum of pressure losses (*quantities.Pressure*) due to fittings/valves in the pipe."""
        return qty.Pressure(self._dp_minor)

    @property
    def pressure_loss(self) -> qty.Pressure:
        """Get the pressure loss (*quantities.Pressure*) across the pipe including its minor losses."""
        dp = 0.0
        if not math.isnan(self._dp_minor):
            dp += self._dp_minor
        if not math.isnan(self._dp_fric):
            dp += self._dp_fric
        return qty.Pressure(dp)

    @property
    def fluid(self) -> Fluid:
        """Get/set the fluid (*pyflow.core.fluids.Fluid*) flowing in the pipe."""
        return self._fluid

    @fluid.setter
    def fluid(self, fl: Fluid):
        self._fluid = fl

    @property
    def cross_section(self) -> Circular:
        """Get/set the cross section (*pyflow.core.cross_sections.Circular*) of the pipe."""
        return self._cross_section

    @cross_section.setter
    def cross_section(self, cs: Circular):
        self._cross_section = cs

    def calculate_diameter(self) -> qty.Length:
        """
        Calculate the diameter of the pipe if flow rate and friction loss are given on creation.

        **Returns:** (*quantities.Length*) = calculated or theoretical inside diameter of the pipe.

        """
        # given: friction loss and flow rate
        rho = self._fluid.density()
        mu = self._fluid.kinematic_viscosity()
        pi = math.pi
        dpf = self._dp_fric
        V = self._flow_rate
        l = self._length
        f = 0.03
        i = 0
        di: float = 0.0
        while i < self._max_iterations:
            di = (f * l / dpf * rho * 8.0 / (pi ** 2.0) * V ** 2.0) ** (1.0 / 5.0)
            A = pi * di ** 2.0 / 4.0
            v = V / A
            re = reynolds_number(v, di, mu)
            rel_pipe_rough = self._rough / di
            f_new = darcy_friction_factor(re, rel_pipe_rough)
            if abs(f_new - f) <= 1.0e-5:
                break
            else:
                f = f_new
                i += 1
                if i == self._max_iterations:
                    raise OverflowError('too many iterations. no solution found')
        self._cross_section.diameter = qty.Length(di)
        return qty.Length(di)

    def calculate_flow_rate(self, sum_zeta: float = 0.0) -> qty.VolumeFlowRate:
        """
        Calculate flow rate through the pipe if nominal diameter and friction loss are known on creation.

        **Parameters:**

        - `sum_zeta`: (*float*) = sum of resistance coefficients of fittings/valves present in the pipe.

        **Returns:** (*quantities.VolumeFlowRate*)

        """
        # given: friction loss and cross section (area and hydraulic diameter)
        rho = self._fluid.density()
        mu = self._fluid.kinematic_viscosity()
        di = self._cross_section.diameter()
        rel_pipe_rough = self._rough / di
        f = 1.325 / math.log10(rel_pipe_rough / 3.7) ** 2.0
        i = 0
        v = 0.0
        while i < self._max_iterations:
            var = f * self._length / di + sum_zeta
            v = math.sqrt(2.0 * self._dp_fric / (rho * var))
            re = reynolds_number(v, di, mu)
            f_new = darcy_friction_factor(re, rel_pipe_rough)
            if abs(f_new - f) <= 1.0e-5:
                break
            else:
                f = f_new
                i += 1
                if i == self._max_iterations:
                    raise OverflowError('too many iterations. no solution found')
        self._flow_rate = self._cross_section.area() * v
        return qty.VolumeFlowRate(self._flow_rate)

    def calculate_pressure_loss(self, sum_zeta: float = 0.0) -> qty.Pressure:
        """
        Calculate pressure loss across the pipe if flow rate and nominal diameter are known on creation.

        **Parameters:**

        - `sum_zeta`: (*float*) = sum of resistance coefficients of fittings/valves present in the pipe.

        **Returns:** (*quantities.Pressure*)

        """
        # given: flow rate and cross section (area and hydraulic diameter)
        rho = self._fluid.density()
        mu = self._fluid.kinematic_viscosity()
        di = self._cross_section.diameter()
        v = self._flow_rate / self._cross_section.area()
        re = reynolds_number(v, di, mu)
        rel_pipe_rough = self._rough / di
        f = darcy_friction_factor(re, rel_pipe_rough)
        self._dp_fric = f * self._length / di * rho * v ** 2.0 / 2.0
        self._dp_minor = sum_zeta * rho * v ** 2.0 / 2.0
        return qty.Pressure(self._dp_fric)
