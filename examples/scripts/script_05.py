"""
DEMO 5
------
Calculate pressure drop in a pipe.
"""
from pypeflow.core import Pipe
from pypeflow.core.fluids import Water
from pypeflow.core.pipe_schedules import PipeSchedule40
import quantities as qty


pipe = Pipe.create(
    fluid=Water(10.0),
    pipe_schedule=PipeSchedule40,
    length=qty.Length(2.7, 'm'),
    flow_rate=qty.VolumeFlowRate(2.180, 'L/s'),
    nominal_diameter=qty.Length(40.0, 'mm'),
    sum_zeta=-0.029
)
print(f'Pressure drop = {pipe.pressure_loss("bar"):.3f} bar.')
