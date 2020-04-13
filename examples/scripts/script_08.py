"""
DEMO 8
------
Create a check valve fitting
"""

import quantities as qty
from pypeflow.core.fitting import Fitting
from pypeflow.core.fluids import Water
from pypeflow.core.cross_sections import Circular
from pypeflow.core.pipe_schedules import PipeSchedule40

flow_rate = qty.VolumeFlowRate(1.696, 'L/s')
cross_section = Circular.create(pipe_schedule=PipeSchedule40, dn=qty.Length(40.0, 'mm'))
velocity = qty.Velocity(flow_rate() / cross_section.area())

check_valve = Fitting.create_w_velocity(
    type_='check_valve',
    fluid=Water(10.0),
    velocity=velocity,
    di=cross_section.diameter,
    ELR=55.0
)

# pressure drop across fitting
dp_fitting = check_valve.pressure_drop
print(f'Pressure drop across check valve = {dp_fitting("Pa"):.3f} Pa')

# resistance coefficient of fitting
zeta = check_valve.zeta
print(f'Resistance coefficient of check valve = {zeta:.3f}')
