"""
DEMO 2
------
Find the pressure drops in the piping network (diameters and flow rates are given).
Add fittings to the sections of a piping network.
Find the flow paths in the piping network.
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
Designer.configure_network('../projects/config2_pressure.csv')
Designer.add_fittings('../projects/config3_fittings.csv')

df1 = Designer.get_sections()
df2 = Designer.get_fittings()
df3 = Designer.get_paths()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df1)
    print()
    print(df2)
    print()
    print(df3)
