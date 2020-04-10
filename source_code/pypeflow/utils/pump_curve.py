"""
## Pump curve fitting and drawing

- Establish an equation for the pump curve from measured points on the curve in the pump's data sheet
- Get the coefficients of the 2nd order polynomial describing the pump curve and determined via curve fitting
- Draw the pump curve in a diagram

"""
from typing import List, Tuple, Dict, Optional
import numpy as np
import quantities as qty
from nummath.interpolation import PolyFit
from nummath.graphing2 import LineGraph


class PumpCurve:

    def __init__(self, dest_units: Dict[str, str]):
        """
        Create *PumpCurve* object.

        **Parameters:**

        - `dest_units`: (*Dict[str, str]*)<br>
        The measuring units in which the pump curve will be expressed. Keys:

            + 'flow_rate'
            + 'pressure'

        """
        self._meas_points: List[Tuple[qty.VolumeFlowRate, qty.Pressure]] = []
        self._dest_units: Dict[str, str] = dest_units
        self._coefficients: Optional[np.array] = None

    def add_measuring_points(self, points: List[Tuple[float, float]], units: Dict[str, str]):
        """
        Add some data points taken from the pump curve in the data sheet. This will execute the curve fitting
        algorithm that approaches the pump curve with a 2nd order polynomial.

        **Parameters:**

        - `points`: (*List[Tuple[float, float]]*)<br>
        List of tuples. The 1st element of the tuple is flow rate, the 2nd element is pressure.
        - `units`: (*Dict[str, str]*)<br>
        Dictionary that contains the measuring units in which the values of the data points are expressed. Keys:

            + 'flow_rate'
            + 'pressure'

        """
        self._meas_points = [
            (qty.VolumeFlowRate(V, units['flow_rate']), qty.Pressure(p, units['pressure'])) for V, p in points
        ]
        self._curve_fitting()

    def _curve_fitting(self):
        pf = PolyFit(
            x_data=[V(self._dest_units['flow_rate']) for V, _ in self._meas_points],
            y_data=[p(self._dest_units['pressure']) for _, p in self._meas_points],
            m=2
        )
        self._coefficients = pf.solve()

    def get_coefficients(self, units: Optional[Dict[str, str]] = None) -> Optional[List[float]]:
        """
        Get the coefficients of the 2nd order polynomial describing the pump curve.

        **Parameters:**

        - `units`: (*Optional[[Dict[str, str]]*)<br>
        Optional dictionary that contains the measuring units in which the returned coefficients must be expressed.
        Default is None, which means that the coefficients will be returned expressed in the measuring units passed in
        at the instantiation of the *PumpCurve* object. Keys:

            + 'flow_rate'
            + 'pressure'

        """
        if units is not None:
            p_src = qty.Pressure(1.0, self._dest_units['pressure'])
            V_src = qty.VolumeFlowRate(1.0, self._dest_units['flow_rate'])
            p_des = p_src(units['pressure'])
            V_des = V_src(units['flow_rate'])
        else:
            p_des = 1.0
            V_des = 1.0
        a0 = self._coefficients[0] * p_des
        a1 = self._coefficients[1] * (p_des / V_des)
        a2 = self._coefficients[2] * (p_des / V_des ** 2)
        return [a0, a1, a2]

    def set_coefficients(self, coeff: Tuple[float, float, float], units: Dict[str, str]):
        """
        Set the known coefficients of the 2nd order polynomial describing the pump curve.

        **Parameters:**

        - `coeff`: (*Tuple[float, float, float]*)<br>
        Tuple of 3 floats: a0, a1 and a2 as in the equation dp_pump = a0 + a1 * V + a2 * V **2
        - `units`: (*Dict[str, str]*)<br>
        Dictionary that contains the measuring units in which the pump coefficients are expressed. Keys:

            + 'flow_rate'
            + 'pressure'

        """
        p_src = qty.Pressure(1.0, units['pressure'])
        V_src = qty.VolumeFlowRate(1.0, units['flow_rate'])
        p_des = p_src(self._dest_units['pressure'])
        V_des = V_src(self._dest_units['flow_rate'])
        a0 = coeff[0] * p_des
        a1 = coeff[1] * (p_des / V_des)
        a2 = coeff[2] * (p_des / V_des ** 2)
        self._coefficients = np.array([a0, a1, a2])

    def create_pump_curve(self, V_initial: qty.VolumeFlowRate, V_final: qty.VolumeFlowRate, num: int = 50):
        """
        Calculate the pump curve between an initial and final flow rate.

        **Parameters:**

        - `V_initial`: (*quantities.VolumeFlowRate*) = initial flow rate
        - `V_final`: (*quantities.VolumeFlowRate*) = final flow rate
        - `num`: (*int*) = number of calculation points (default = 50)

        **Returns:** (*Tuple[np.array, np.array]*)
        Tuple with 1st element a numpy array of the flow rates and 2nd element a numpy array of the corresponding
        pressures, both expressed in the desired measuring units set at instantiation of the *PumpCurve*-object.

        """
        V_i = V_initial(self._dest_units['flow_rate'])
        V_f = V_final(self._dest_units['flow_rate'])
        V = np.linspace(V_i, V_f, num, endpoint=True)
        a0 = self._coefficients[0]; a1 = self._coefficients[1]; a2 = self._coefficients[2]
        p = a0 + a1 * V + a2 * V ** 2
        return V, p

    def draw_pump_curve(self, V_initial: qty.VolumeFlowRate, V_final: qty.VolumeFlowRate, **kwargs):
        """
        Draw the calculated pump curve.

        **Parameters:**

        - `V_initial`: (*quantities.VolumeFlowRate*) = initial flow rate
        - `V_final`: (*quantities.VolumeFlowRate*) = final flow rate
        - `kwargs`: optional keyword arguments
            + `fig_size`: (*Tuple[float, float]*) = the width and height of the figure in inches
            + `dpi`: (*int*) = dots per inch of the figure
            + `num`: (*int*) = number of calculated points to draw
            + `V_step`: (*quantities.VolumeFlowRate*) = step between ticks on the flow rate axis of the diagram
            + `V_max`: (*quantities.VolumeFlowRate*) = the maximum flow rate shown on the axis
            + `p_step`: (*quantities.Pressure*) = step between ticks on the pressure axis of the diagram
            + `p_max`: (*quantities.Pressure*) = maximum pressure shown on the axis
            + `working_point`: (*Tuple[qty.VolumeFlowRate, qty.Pressure]*) = working point of the pump (shown as a red
            dot on the diagram)

        **Returns:** (*nummath.graphing2.LineGraph*)<br>
        Call show() on the returned *LineGraph* object to show the diagram.
        """
        if self._coefficients is not None:
            fig_size: Tuple[int, int] = kwargs.get('fig_size', (6, 4))
            dpi: int = kwargs.get('dpi', 96)
            num: int = kwargs.get('num', 50)
            V_step: qty.VolumeFlowRate = kwargs.get('V_step')
            V_max: qty.VolumeFlowRate = kwargs.get('V_max')
            p_step: qty.Pressure = kwargs.get('p_step')
            p_max: qty.Pressure = kwargs.get('p_max')
            working_point: Tuple[qty.VolumeFlowRate, qty.Pressure] = kwargs.get('working_point')
            V, p = self.create_pump_curve(V_initial, V_final, num)
            graph = LineGraph(fig_size=fig_size, dpi=dpi)
            graph.add_dataset(name="pump curve", x1_data=V, y1_data=p)
            if self._meas_points:
                graph.add_dataset(
                    name="measured points",
                    x1_data=[V(self._dest_units['flow_rate']) for V, _ in self._meas_points],
                    y1_data=[p(self._dest_units['pressure']) for _, p in self._meas_points],
                    layout={'marker': 'o', 'linestyle': 'None'}
                )
            if working_point:
                graph.add_dataset(
                    name="working point",
                    x1_data=working_point[0](self._dest_units['flow_rate']),
                    y1_data=working_point[1](self._dest_units['pressure']),
                    layout={'marker': 'o', 'linestyle': 'None', 'color': 'red'}
                )
            graph.x1.set_title(f'flow rate [{self._dest_units["flow_rate"]}]')
            if V_max is not None and V_step is not None:
                graph.x1.scale(
                    lim_down=0.0,
                    lim_up=V_max(self._dest_units['flow_rate']),
                    step_size=V_step(self._dest_units['flow_rate'])
                )
            graph.y1.set_title(f'pressure [{self._dest_units["pressure"]}]')
            if p_max is not None and p_step is not None:
                graph.y1.scale(
                    lim_down=0.0,
                    lim_up=p_max(self._dest_units['pressure']),
                    step_size=p_step(self._dest_units['pressure'])
                )
            return graph

    def pump_head(self, V: qty.VolumeFlowRate) -> qty.Pressure:
        """
        Get the pump head (*quantities.Pressure*) if the flow rate (*quantities.VolumeFlowRate*) is given.

        """
        a0 = self._coefficients[0]
        a1 = self._coefficients[1]
        a2 = self._coefficients[2]
        V = V(self._dest_units['flow_rate'])
        return qty.Pressure(a0 + a1 * V + a2 * V ** 2, self._dest_units['pressure'])


if __name__ == '__main__':

    pump_curve = PumpCurve(dest_units={'flow_rate': 'L/s', 'pressure': 'bar'})
    pump_curve.add_measuring_points(
        points=[(0.0, 60.0), (2.4, 52.0), (4.2, 48.0), (6.0, 36.0)],
        units={'flow_rate': 'm^3/h', 'pressure': 'm'}
    )

    coeff1 = pump_curve.get_coefficients(units={'pressure': 'Pa', 'flow_rate': 'm^3/s'})
    print(coeff1)
    coeff2 = pump_curve.get_coefficients(units={'pressure': 'bar', 'flow_rate': 'L/s'})
    print(coeff2)

    graph_ = pump_curve.draw_pump_curve(
        V_initial=qty.VolumeFlowRate(0.0, 'm^3/h'),
        V_final=qty.VolumeFlowRate(7.2, 'm^3/h'),
        fig_size=(10, 8),
        dpi=150,
        num=100,
        V_max=qty.VolumeFlowRate(3.0, 'L/s'),
        V_step=qty.VolumeFlowRate(0.5, 'L/s'),
        p_max=qty.Pressure(8.0, 'bar'),
        p_step=qty.Pressure(2.0, 'bar')
    )
    graph_.show()
