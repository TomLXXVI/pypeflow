"""
DEMO 6
------
Calculate flow coefficient and resistance coefficient of draw-off point from known flow rate and pressure drop.
"""
import quantities as qty
from pypeflow.core.flow_coefficient import FlowCoefficient
from pypeflow.core.resistance_coefficient import ResistanceCoefficient
from pypeflow.core.pipe_schedules import PipeSchedule40


V = qty.VolumeFlowRate(0.29, 'L/s')
dp = qty.Pressure(0.05, 'MPa')
Kv = FlowCoefficient.calc_Kv(V, dp)
print(f'flow coefficient = {Kv:.3f}')

di = PipeSchedule40.inside_diameter(DN=qty.Length(15.0, 'mm'))
print(f'inside diameter = {di("mm"):.3f} mm')

zeta = ResistanceCoefficient.from_Kv(Kv, di)
print(f'resistance coefficient = {zeta:.3f}')

