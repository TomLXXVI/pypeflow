"""
DEMO 3
------
Adding control valves to cross-overs in piping network
Balance a piping network.
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
Designer.configure_network('../projects/config2_bal_pressure.csv')

cross_overs = ['s22*', 's33*', 's44*', 's55*', 's66*', 's77*', 's88*', 's99*']
Kvs_pre_list = Designer.add_balancing_valves([(cross_over, 0.03) for cross_over in cross_overs])
print('Calculated preliminary Kvs values for balancing valves')
for Kvs in Kvs_pre_list:
    print(Kvs)
print()

Designer.init_balancing_valves([(cross_over, 5.70) for cross_over in cross_overs])

print('Kvr values of balancing valves to obtain flow balancing')
Kvr_list = Designer.set_balancing_valves()
for Kvr in Kvr_list:
    print(Kvr)
print()

print('Calculated preliminary Kvs values for control valves')
Kvs_pre_list = Designer.add_control_valves([(cross_over, 0.5) for cross_over in cross_overs])
for Kvs in Kvs_pre_list:
    print(Kvs)
print()

Designer.set_control_valves([(cross_over, 1.0) for cross_over in cross_overs])

df1 = Designer.get_balancing_valves()
df2 = Designer.get_control_valves()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df1)
    print()
    print(df2)
print()

df3 = Designer.get_sections()
df4 = Designer.get_paths()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df3)
    print()
    print(df4)
    print()
