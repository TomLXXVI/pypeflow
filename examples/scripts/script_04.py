"""
DEMO 4
------
Network analysis with Hardy Cross.
"""

import pandas as pd
from pypeflow.analysis.analysis import Analyzer


Analyzer.set_units({
    'length': 'm',
    'diameter': 'mm',
    'flow_rate': 'L/s',
    'pressure': 'bar',
    'velocity': 'm/s'
})
Analyzer.create_network(
    start_node_id='n1',
    end_node_id='n0',
    fluid='water',
    fluid_temperature=10.0,
    pipe_schedule='pipe_schedule_40'
)
Analyzer.configure_network('../projects/config4_hardy.csv')
Analyzer.solve(error=1.0e-3, i_max=5000)
df1 = Analyzer.get_network()
df2 = Analyzer.get_paths()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df1)
    print()
    print(df2)
