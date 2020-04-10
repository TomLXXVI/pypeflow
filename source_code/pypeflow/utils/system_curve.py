"""
## Calculate and draw the system curve of a flow path in a piping network

"""
from typing import Dict, Tuple
import numpy as np
import quantities as qty
from nummath.graphing2 import LineGraph


class SystemCurve:

    def __init__(self, R_hyd: float, src_units: Dict[str, str], dest_units: Dict[str, str]):
        """
        Create *SystemCurve* object.

        **Parameters:**

        - `R_hyd`: (*float*) = (equivalent) hydraulic resistance of flow path
        - `src_units`: (*Dict[str, str]*) = the measuring units associated with the hydraulic resistance. Keys:
            + 'flow_rate'
            + 'pressure'
        - `dest_units`: (*Dict[str, str]*) = the desired measuring units in which to express the system curve

        """
        self._R_hyd: float = R_hyd
        self._V_unit: str = src_units['flow_rate']
        self._p_unit: str = src_units['pressure']
        self._dest_units: Dict[str, str] = dest_units
        self._dp_stat: float = 0.0
        self._dp_elev: float = 0.0

    def set_static_head(self, p_stat: qty.Pressure):
        """Set static head (*quantities.Pressure*) of flow path."""
        self._dp_stat: float = p_stat(self._p_unit)

    def set_elevation_head(self, p_elev: qty.Pressure):
        """Set elevation head (*quantities.Pressure*) of flow path."""
        self._dp_elev: float = p_elev(self._p_unit)

    def create_system_curve(self, V_initial: qty.VolumeFlowRate, V_final: qty.VolumeFlowRate, num: int = 50):
        """
        Calculate the system curve between an initial and final flow rate.

        **Parameters:**

        - `V_initial`: (*quantities.VolumeFlowRate*) = initial flow rate
        - `V_final`: (*quantities.VolumeFlowRate*) = final flow rate
        - `num`: (*int*) = number of calculation points (default = 50)

        **Returns:** (*Tuple[np.array, np.array]*)
        Tuple with 1st element a numpy array of the flow rates and 2nd element a numpy array of the corresponding
        pressures, both expressed in the desired measuring units set at instantiation of the *SystemCurve*-object.

        """
        V_i = V_initial(self._V_unit)
        V_f = V_final(self._V_unit)
        V_arr = np.linspace(V_i, V_f, num, endpoint=True)
        p_arr = self._R_hyd * V_arr ** 2 + self._dp_stat + self._dp_elev
        V_qty = [qty.VolumeFlowRate(V, self._V_unit) for V in V_arr]
        p_qty = [qty.Pressure(p, self._p_unit) for p in p_arr]
        V_sys = [V(self._dest_units['flow_rate']) for V in V_qty]
        p_sys = [p(self._dest_units['pressure']) for p in p_qty]
        return V_sys, p_sys

    def draw_system_curve(self, V_initial: qty.VolumeFlowRate, V_final: qty.VolumeFlowRate, **kwargs) -> LineGraph:
        """
        Draw the calculated system curve.

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

        **Returns:** (*nummath.graphing2.LineGraph*)<br>
        Call show() on the returned *LineGraph* object to show the diagram.
        """
        fig_size: Tuple[int, int] = kwargs.get('fig_size', (6, 4))
        dpi: int = kwargs.get('dpi', 96)
        num: int = kwargs.get('num', 50)
        V_step: qty.VolumeFlowRate = kwargs.get('V_step')
        V_max: qty.VolumeFlowRate = kwargs.get('V_max')
        p_step: qty.Pressure = kwargs.get('p_step')
        p_max: qty.Pressure = kwargs.get('p_max')
        V, p = self.create_system_curve(V_initial, V_final, num)
        graph = LineGraph(fig_size=fig_size, dpi=dpi)
        graph.add_dataset(name="system curve", x1_data=V, y1_data=p)
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
