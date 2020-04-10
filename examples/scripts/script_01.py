"""
DEMO 1
------
Find the nominal piping diameters in a piping network.
"""

import pandas as pd
from pypeflow.design import Designer

Designer.set_units({
    'length': 'm',
    'diameter': 'mm',
    'flow_rate': 'L/s',
    'pressure': 'bar',
    'velocity': 'm/s'
})
Designer.create_network(
    start_node_id='n1',
    end_node_id='n0',
    fluid='water',
    fluid_temperature=10.0,
    pipe_schedule='pipe_schedule_40'
)
Designer.configure_network('../projects/config1_diameters.csv')

df = Designer.get_sections()

with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df)
