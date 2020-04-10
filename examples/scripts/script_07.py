"""
DEMO 7
------
Calculate resistance coefficient of elbow from ELR coefficient (Crane-K-method)
"""

import quantities as qty
from pypeflow.core.resistance_coefficient import ResistanceCoefficient
from pypeflow.core.pipe_schedules import PipeSchedule40

ELR_elbow = 30.0  # see Crane Technical Paper, appendix A
di = PipeSchedule40.inside_diameter(DN=qty.Length(15.0, 'mm'))
zeta_elbow = ResistanceCoefficient.from_ELR(ELR=ELR_elbow, di=di)
print(f'resistance coefficient elbow = {zeta_elbow:.3f}')
