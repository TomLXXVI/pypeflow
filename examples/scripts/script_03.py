"""
DEMO 3
------
Adding control valves to cross-overs in piping network
Balance a piping network.
"""
import pandas as pd
import quantities as qty
from pypeflow.design import Designer
from pypeflow.utils import SystemCurve


print('SETTING UP THE DESIGNER')
print('-----------------------')
print()

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

df_paths = Designer.get_paths()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df_paths)
    print()

print('ADDING BALANCING VALVES')
print('-----------------------')
print()

cross_overs = ['s22*', 's33*', 's44*', 's55*', 's66*', 's77*', 's88*', 's99*']

Kvs_pre_list = Designer.add_balancing_valves([(x, 0.03) for x in cross_overs])
print('Calculated preliminary Kvs values for balancing valves')
for Kvs in Kvs_pre_list:
    print(Kvs)
print()

Kvs_bal = float(input('Enter commercially available Kvs: '))
Designer.init_balancing_valves([(x, Kvs_bal) for x in cross_overs])
print()

df_paths = Designer.get_paths()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df_paths)
    print()

print('ADDING CONTROL VALVES TO THE CROSS-OVERS')
print('----------------------------------------')
print()

print('Calculated preliminary Kvs values for control valves')
Kvs_pre_list = Designer.add_control_valves([(x, 0.5) for x in cross_overs])
for Kvs in Kvs_pre_list:
    print(Kvs)
print()

Kvs_cv = float(input('Enter commercially available Kvs: '))
Designer.set_control_valves([(x, Kvs_cv) for x in cross_overs])
print()

df_paths = Designer.get_paths()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df_paths)
    print()

print('BALANCE THE NETWORK')
print('-------------------')
print()

print('Kvr values of balancing valves to obtain flow balancing')
Kvr_list = Designer.set_balancing_valves()
for Kvr in Kvr_list:
    print(Kvr)
print()

print('GET RESULTS')
print('-----------')
print()

print('Balancing valves')
print()
df1 = Designer.get_balancing_valves()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df1)
    print()

print('Control valves')
print()
df2 = Designer.get_control_valves()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df2)
    print()

print('Pipe sections')
print()
df3 = Designer.get_sections()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df3)
    print()

print('Flow paths')
print()
df4 = Designer.get_paths()
with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 320):
    print(df4)
    print()

print('DRAW THE SYSTEM CURVE')
print('---------------------')

R_hyd = Designer.network.hydraulic_resistance
system_curve = SystemCurve(R_hyd, {'flow_rate': 'm^3/s', 'pressure': 'Pa'}, {'flow_rate': 'L/s', 'pressure': 'bar'})
graph = system_curve.draw_system_curve(
    V_initial=qty.VolumeFlowRate(0.0, 'L/s'),
    V_final=qty.VolumeFlowRate(2.5, 'L/s'),
    V_max=qty.VolumeFlowRate(2.5, 'L/s'),
    V_step=qty.VolumeFlowRate(0.2, 'L/s')
)
graph.show()
