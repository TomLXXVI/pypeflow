"""
## Modeling a balancing valve and control valve in a pipe section
"""
from typing import Optional
import math
import quantities as qty
from pypeflow.core.fluids import Fluid
from pypeflow.core.flow_coefficient import FlowCoefficient


class BalancingValve:
    """
    Class that models a balancing valve.
    """

    def __init__(self):
        self._fluid: Optional[Fluid] = None
        self._dp: float = math.nan
        self._flow_rate: float = math.nan
        self._Kvs: float = math.nan
        self._Kvr: float = math.nan
        self._dp_excess: float = math.nan

    @classmethod
    def create(cls, fluid: Fluid, flow_rate: qty.VolumeFlowRate, dp_100: qty.Pressure) -> 'BalancingValve':
        """
        Create configured balancing valve.

        **Parameters:**

        - `fluid`: (*pyflow.core.fluids.Fluid*) = fluid through balancing valve
        - `flow_rate`: (*quantities.VolumeFlowRate*) = flow rate through balancing valve
        - `dp_100`: (*quantities.Pressure*) = design pressure drop across balancing valve when fully open (100 % open).

        Based on design pressure drop and flow rate a preliminary Kvs value is calculated.

        **Returns:** (object of class *BalancingValve*)

        """
        bv = cls()
        bv._fluid = fluid
        bv._flow_rate = flow_rate()
        bv._dp = dp_100()
        bv._calc_preliminary_Kvs()
        return bv

    def _calc_preliminary_Kvs(self):
        Avs = self._flow_rate / math.sqrt(self._dp / self._fluid.density('kg/m^3'))
        self._Kvs = FlowCoefficient.Av_to_Kv(Avs)

    @property
    def pressure_drop(self) -> qty.Pressure:
        """Get pressure drop (*quantities.Pressure*) across balancing valve."""
        return qty.Pressure(self._dp)

    @property
    def Kvs(self) -> float:
        """
        Get/set (commercial available) Kvs value (*float*) of fully opened balancing valve.
        When set, the actual pressure drop across the balancing valve is recalculated.
        """
        return self._Kvs

    @Kvs.setter
    def Kvs(self, Kvs_: float):
        self._Kvs = Kvs_
        Avs = FlowCoefficient.Kv_to_Av(self._Kvs)
        # update pressure drop across valve
        self._dp = self._fluid.density('kg/m^3') * (self._flow_rate / Avs) ** 2

    def set_pressure_excess(self, dp_excess: qty.Pressure):
        """
        Set the amount of pressure (*float*) that must be dissipated by the balancing valve.
        The Kvr setting of the balancing valve will also be calculated.

        """
        self._dp_excess = dp_excess('Pa')
        self._calc_required_Kvr()

    def _calc_required_Kvr(self):
        self._dp += self._dp_excess
        Avr = self._flow_rate / math.sqrt(self._dp / self._fluid.density('kg/m^3'))
        self._Kvr = FlowCoefficient.Av_to_Kv(Avr)

    @property
    def Kvr(self) -> float:
        """
        Get Kv value (*float*) of balancing valve needed to dissipate pressure excess.
        """
        return self._Kvr


class ControlValve:
    """
    Class that models a control valve.
    """

    def __init__(self):
        self._fluid: Optional[Fluid] = None
        self._flow_rate: float = math.nan
        self._dp: float = math.nan
        self._Kvs: float = math.nan
        self._target_authority: float = math.nan
        self._dp_crit_path: float = math.nan

    @classmethod
    def create(cls, fluid: Fluid, flow_rate: qty.VolumeFlowRate, target_authority: float,
               dp_crit_path: qty.Pressure) -> 'ControlValve':
        """
        Create configured ControlValve object.<br>
        Based on target authority and section pressure loss a preliminary Kvs value is calculated.

        **Parameters:**

        - `fluid`: (object of type *pyflow.core.fluids.Fluid*) = fluid through control valve
        - `flow_rate`: (*quantities.VolumeFlowRate*) = flow rate through control valve
        - `target_authority`: (*float*) = target authority of control valve at design
        - `dp_crit_path`: (*quantities.Pressure*) = pressure loss in the critical path of the network

        **Returns:** (*ControlValve* object)

        """
        cv = cls()
        cv._fluid = fluid
        cv._flow_rate = flow_rate()
        cv._target_authority = target_authority
        cv._dp_crit_path = dp_crit_path()
        cv._calc_preliminary_Kvs()
        return cv

    def _calc_preliminary_Kvs(self):
        # don't store the pressure drop across the control valve when the preliminary Kvs value is calculated, keep it
        # local to the method
        dp = self._target_authority * self._dp_crit_path / (1.0 - self._target_authority)
        Avs = self._flow_rate / math.sqrt(dp / self._fluid.density('kg/m^3'))
        self._Kvs = FlowCoefficient.Av_to_Kv(Avs)

    def authority(self, dp_crit_path: qty.Pressure) -> float:
        """
        Get control valve authority (*float*) given the pipe section pressure loss (*quantities.Pressure*).
        """
        return self._dp / dp_crit_path()

    @property
    def Kvs(self) -> float:
        """
        Get/set (commercial available) Kvs value (*float*) of control valve.
        When set, the pressure drop across the control valve is recalculated.
        """
        return self._Kvs

    @Kvs.setter
    def Kvs(self, Kvs_: float):
        """
        Set  Kvs value (*float*) of control valve.
        """
        self._Kvs = Kvs_
        Avs = FlowCoefficient.Kv_to_Av(self._Kvs)
        # update pressure drop across control valve
        self._dp = self._fluid.density('kg/m^3') * (self._flow_rate / Avs) ** 2

    @property
    def pressure_drop(self) -> qty.Pressure:
        """Get pressure drop (*quantities.Pressure*) across control valve."""
        return qty.Pressure(self._dp)
