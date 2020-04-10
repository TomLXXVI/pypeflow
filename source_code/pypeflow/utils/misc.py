"""
## Miscellaneous utility functions.
"""
import quantities as qty
from pypeflow.core.fluids import Water


def calc_specific_friction_loss(**kwargs):
    """
    Calculate the pressure drop per metre length of pipe that remains available for friction loss and that can to used
    to determine appropriate pipe diameters.

    **kwargs:**

    - `path_length`: (*float*) = total pipe length from point immediately downstream water meter up to the
    draw-off-point [m]
    - `p_supply_min`: (*float*) = minimum available supply pressure [Pa]
    - `p_draw_off_req`: (*float*) = required minimum flow pressure at draw-off point [Pa]
    - `height`: (*float*) = elevation of draw-off point with respect to supply entrance (i.e static head) [m]
    - `dp_appliance`: (*float*) = sum of pressure losses in appliances @ design flow rate [Pa]
    - `dp_check_valve`: (*float*) = sum of pressure losses due to resistance of check valves @ design flow rate [Pa]
    - `dp_fittings_per`: (*float*) = percentage of pressure loss due to fittings [%]

    **Returns:** (*Tuple[qty.Pressure, qty.Pressure]*)<br>

    - frictional pressure drop per metre that remains available for pipe sizing.
    - total available frictional pressure drop along flow path

    """
    dp_fittings_per = kwargs.get('dp_fittings_per', 0.0)
    path_length = kwargs.get('path_length', 0.0)
    p_supply_min = kwargs.get('p_supply_min', 0.0)
    height = kwargs.get('height', 0.0)
    dp_appliance = kwargs.get('dp_appliance', 0.0)
    dp_check_valve = kwargs.get('dp_check_valve', 0.0)
    p_draw_off_req = kwargs.get('p_draw_off_req')

    fluid = Water(10.0)
    g = 9.81
    rho = fluid.density('kg/m^3')
    static_head = rho * g * height
    total_head_req = p_supply_min - p_draw_off_req
    # head that remains available for friction loss
    fric_head_av = total_head_req - static_head - dp_appliance - dp_check_valve
    fric_head_av = (1.0 - dp_fittings_per / 100.0) * fric_head_av  # subtract fitting losses
    # pressure drop per metre pipe length available for friction loss
    dp_fric_spec = fric_head_av / path_length  # Pa / m
    return qty.Pressure(dp_fric_spec), qty.Pressure(fric_head_av)