"""
## User interface for designing a piping network
"""
from typing import Type, Dict, List, Tuple
import csv
import math
import pandas as pd
import quantities as qty
from pypeflow.core.pipe_schedules import PipeSchedule, PIPE_SCHEDULES
from pypeflow.core.fluids import Fluid, FLUIDS
from pypeflow.design.network import Network


class Designer:
    """
    Class that encapsulates the user interface methods
    """
    network: Network = Network()
    """Reference to the *Network* object"""
    units: Dict[str, str] = {
        'length': 'm',
        'diameter': 'mm',
        'flow_rate': 'L/s',
        'pressure': 'bar',
        'velocity': 'm/s',
        'height': 'm'
    }
    """Dictionary that holds the measuring units in which the quantity values are expressed"""

    @classmethod
    def set_units(cls, units: Dict[str, str]):
        """
        Set the measuring SI-units of the quantities that will be used as input and that will be returned as output.

        Parameter `units` is a dictionary (*Dict[str, str]*) that can contain the following keys with corresponding
        measuring units assigned to them:

        - *'length'* (default value = *'m'*)
        - *'diameter'* (default value = *'mm'*)
        - *'flow_rate'* (default value = *'L/s'*)
        - *'pressure'* (default value = *'bar'*)
        - *'velocity'* (default value = *'m/s'*)

        """
        cls.units.update(units)

    @classmethod
    def create_network(cls, **kwargs):
        """
        Create piping network.

        **kwargs:**

        - `start_node_id`: (*str*) = id of the start node of the network
        - `end_node_id`: (*str*) = id of the exit node of the network
        - `fluid`: (*str*) = fluid that flows in the network (available fluids: 'water'/'air', default = 'water')
        - `fluid_temperature`: (*float*) = reference temperature of fluid used to determine other fluid properties
        (density, viscosity)
        - `pipe_schedule`: (*str*) = pipe schedule of pipe sections (to determine cross section dimensions and
        pipe wall roughness)

        """
        start_node_id: str = kwargs.get('start_node_id')
        end_node_id: str = kwargs.get('end_node_id')
        fluid: str = kwargs.get('fluid', 'water')
        fluid_temperature: float = kwargs.get('fluid_temperature', 10.0)
        pipe_schedule: str = kwargs.get('pipe_schedule', 'pipe_schedule_40')
        fluid_obj = cls._create_fluid(fluid, fluid_temperature)
        pipe_schedule_type = cls._create_pipe_schedule(pipe_schedule)
        cls.network = Network.create(
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            fluid=fluid_obj,
            pipe_schedule=pipe_schedule_type
        )

    @staticmethod
    def _create_fluid(fluid: str, temperature: float) -> Fluid:
        """Create Fluid object from given fluid string and temperature."""
        try:
            fluid_type = FLUIDS[fluid.lower()]
        except KeyError:
            raise KeyError(f'Fluid {fluid} unknown.')
        else:
            return fluid_type(temperature)

    @staticmethod
    def _create_pipe_schedule(pipe_schedule: str) -> Type[PipeSchedule]:
        """Get PipeSchedule derived class from pipe schedule string."""
        try:
            pipe_schedule_type = PIPE_SCHEDULES[pipe_schedule.lower()]
        except KeyError:
            raise KeyError(f'Pipe schedule {pipe_schedule} unknown.')
        else:
            return pipe_schedule_type

    @classmethod
    def configure_network(cls, file_path: str):
        """
        Configure network via a network configuration file (.csv-file). Parameter `file_path` (*str*) is the file path
        to this configuration file. The configuration data is organised in a table. Each row contains the configuration
        data of a pipe section in the network. Each row has the following fields (columns) in the order as
        mentioned here:

        0. id of the section
        1. start node id of the section
        2. height of the start node with respect to a chosen reference plane
        3. end node id of the section
        4. height of the end node with respect to a chosen reference plane
        5. length of the section
        6. nominal diameter (leave empty if not known)
        7. design flow rate through the section
        8. pressure drop across section due to friction (leave empty if not known)

        Designing a network implies solving two kind of problems:

        1. Diameter and flow rate are known -> find the pressure drop across the section<br>
        2. Friction loss and flow rate are known -> find the calculated, theoretical inside diameter

        """
        with open(file_path) as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == 0:
                    continue
                else:
                    cls.network.add_section(
                        id=row[0],
                        start_node_id=row[1],
                        start_node_height=qty.create(qty.Length, row[2], cls.units['length'], 0.0),
                        end_node_id=row[3],
                        end_node_height=qty.create(qty.Length, row[4], cls.units['length'], 0.0),
                        length=qty.create(qty.Length, row[5], cls.units['length'], 0.0),
                        nominal_diameter=qty.create(qty.Length, row[6], cls.units['diameter'], None),
                        flow_rate=qty.create(qty.VolumeFlowRate, row[7], cls.units['flow_rate'], None),
                        pressure_drop=qty.create(qty.Pressure, row[8], cls.units['pressure'], None),
                    )

    @classmethod
    def add_fittings(cls, file_path: str):
        """
        Add fittings/valves to the sections of the piping network. Fitting data is read from a .csv-file.  Parameter
        `file_path` (*str*) is the file path to this fitting data file. The fitting data is organised in a table.
        Each row contains the data of one fitting. Each row has the following fields (columns) in the order as
        mentioned here:

        0. id of the section to which the fitting/valve belongs
        1. id of the fitting
        2. type of the fitting (can be chosen arbitrarily, just a description for easy reference)
        3. *zeta* resistance coefficient
        4. *zeta_inf* resistance coefficient (see 3K-method)
        5. *zeta_d* resistance coefficient (see 3K-method)
        6. *ELR* equivalent length ratio (see Crane-K-method)
        7. *Kv* flow coefficient (based on flow rate in m^3/h and pressure in bar)

        At least one resistance coefficient (or flow coefficient) must be specified. In case of the 3K-method, *zeta*,
        *zeta_inf* and *zeta_d* must be specified. Leave other fields empty if they are not used.

        """
        with open(file_path) as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == 0:
                    continue
                else:
                    section_id = row[0]
                    section = cls.network.sections[section_id]
                    if section.real:
                        section.add_fitting(
                            id=row[1],
                            type=row[2],
                            zeta=cls._set_float(row[3]),
                            zeta_inf=cls._set_float(row[4]),
                            zeta_d=cls._set_float(row[5]),
                            ELR=cls._set_float(row[6]),
                            Kv=cls._set_float(row[7]),
                        )

    @staticmethod
    def _set_float(value: str) -> float:
        try:
            value = float(value)
        except ValueError:
            return math.nan
        else:
            return value

    @classmethod
    def add_balancing_valves(cls, dp_100_list: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """
        Add one or more balancing valves to the network.

        **Parameters:**

        - `dp_100_list`: (*List[Tuple[str, float]]*)<br>
        List of tuples. The first element (*str*) of the tuple is the id of the section to which the balancing valve
        must be added. The second element (*float*) is the design pressure drop across the fully open balancing valve.
        The measuring unit is taken from the units set (see method `set_units`).

        **Returns:** (*List[Tuple[str, float]]*)<br>
        List of tuples. The first element (*str*) of the tuple is the id of the section to which the balancing valve is
        added. The second element (*float*) is the preliminary Kvs value of the balancing valve.

        """
        Kvs_pre_list: List[Tuple[str, float]] = []
        for section_id, dp_100 in dp_100_list:
            section = cls.network.sections[section_id]
            Kvs_pre = section.add_balancing_valve(qty.Pressure(dp_100, cls.units['pressure']))
            Kvs_pre_list.append((section_id, Kvs_pre))
        return Kvs_pre_list

    @classmethod
    def init_balancing_valves(cls, Kvs_list: List[Tuple[str, float]]):
        """
        Set the commercial available Kvs values of the balancing valves in the network.

        **Parameters:**

        - `Kvs_list`: (*List[Tuple[str, float]]*)<br>
        List of tuples. The first element (*str*) of the tuple is the id of the section to which the balancing valve was
        added. The second element (*float*) is the Kvs value of the balancing valve.

        """
        for section_id, Kvs in Kvs_list:
            section = cls.network.sections[section_id]
            section.init_balancing_valve(Kvs)

    @classmethod
    def add_control_valves(cls, target_authority_list: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """
        Add one ore more control valves to the network.

        **Parameters:**

        - `target_authority_list`: (*List[Tuple[str, float]]*)<br>
        List of tuples. The first element (*str*) of the tuple is the id of the section to which the control valve was
        added. The second element (*float*) is the valve authority aimed at.

        **Returns:** (*List[Tuple[str, float]]*)<br>
        List of tuples. The first element (*str*) of the tuple is the id of the section to which the control valve is
        added. The second element (*float*) is the preliminary Kvs value of the control valve.

        """
        Kvs_pre_list: List[Tuple[str, float]] = []
        for section_id, target_authority in target_authority_list:
            section = cls.network.sections[section_id]
            Kvs = section.add_control_valve(target_authority)
            Kvs_pre_list.append((section_id, Kvs))
        return Kvs_pre_list

    @classmethod
    def set_control_valves(cls, Kvs_list: List[Tuple[str, float]]):
        """
        Set the commercial available Kvs value of the control valves in the network.

        **Parameters:**

        - `Kvs_list`: (*List[Tuple[str, float]]*)<br>
        List of tuples. The first element (*str*) of the tuple is the id of the section to which the control valve was
        added. The second element (*float*) is the Kvs value of the control valve.

        """
        for section_id, Kvs in Kvs_list:
            section = cls.network.sections[section_id]
            section.set_control_valve(Kvs)

    @classmethod
    def set_balancing_valves(cls) -> List[Tuple[str, float]]:
        """
        Calculate the Kvr setting of the balancing valves in the network in order to dissipate excess feed pressure.

        **Returns:** (*List[Tuple[str, float]]*)<br>
        List of tuples. The first element (*str*) of the tuple is the id of the section to which the balancing valve was
        added. The second element (*float*) is the calculated Kvr setting of the balancing valve.

        """
        Kvr_list: List[Tuple[str, float]] = []
        bv_dict = cls.network.get_balancing_valves()
        dp_max = cls.network.critical_path.static_head_required()
        for section_id in bv_dict.keys():
            section = cls.network.sections[section_id]
            dp_path = bv_dict[section_id][1].static_head_required()
            section.set_balancing_valve(qty.Pressure(dp_max - dp_path))
            Kvr_list.append((section_id, section.balancing_valve.Kvr))
        return Kvr_list

    @classmethod
    def get_sections(cls) -> pd.DataFrame:
        """
        Returns an overview of the sections in the network organised in a Pandas DataFrame.
        """
        keys = [
            'section_id',
            f'L [{cls.units["length"]}]',
            f'Di,th [{cls.units["diameter"]}]',
            f'Di [{cls.units["diameter"]}]',
            f'DN [{cls.units["diameter"]}]',
            f'V [{cls.units["flow_rate"]}]',
            f'v [{cls.units["velocity"]}]',
            f'dp,dyn [{cls.units["pressure"]}]',
        ]
        d = {k: [] for k in keys}
        for section in cls.network.sections.values():
            d[keys[0]].append(section.id)
            d[keys[1]].append(section.pipe.length(cls.units['length'], 3))
            d[keys[2]].append(section.pipe.cross_section.calculated_diameter(cls.units['diameter'], 3))
            d[keys[3]].append(section.pipe.cross_section.diameter(cls.units['diameter'], 3))
            d[keys[4]].append(section.pipe.cross_section.nominal_diameter(cls.units['diameter'], 3))
            d[keys[5]].append(section.pipe.flow_rate(cls.units['flow_rate'], 3))
            d[keys[6]].append(section.pipe.velocity(cls.units['velocity'], 3))
            d[keys[7]].append(section.pressure_drop(cls.units['pressure'], 3))
        return pd.DataFrame(d)

    @classmethod
    def get_paths(cls) -> pd.DataFrame:
        """
        Returns an overview of the flow paths in the network organised in a Pandas DataFrame.

        Following data about the flow paths is returned:

        - velocity head loss between end node and start node of the path
        - elevation head loss between end node and start node of the path
        - dynamic head loss between end node and start of the path
        - static head required between start node and end node of flow path to establish the design flow rates along the
        path
        - the pressure difference between the critical path and the path under consideration (after balancing the
        network for design flow rates, there should be zero difference)

        """
        keys = [
            'path',
            f'dp,vel [{cls.units["pressure"]}]',
            f'dp,elev [{cls.units["pressure"]}]',
            f'dp,dyn [{cls.units["pressure"]}]',
            f'dp,stat req. [{cls.units["pressure"]}]',
            f'dp,dif [{cls.units["pressure"]}]'
        ]
        d = {k: [] for k in keys}
        static_head_max = cls.network.critical_path.static_head_required
        for path in cls.network.paths:
            d[keys[0]].append(repr(path))
            d[keys[1]].append(path.velocity_head(cls.units['pressure'], 3))
            d[keys[2]].append(path.elevation_head(cls.units['pressure'], 3))
            d[keys[3]].append(path.dynamic_head(cls.units['pressure'], 3))
            d[keys[4]].append(path.static_head_required(cls.units['pressure'], 3))
            dp_dif = qty.Pressure(static_head_max() - path.static_head_required())
            d[keys[5]].append(dp_dif(cls.units['pressure'], 3))
        return pd.DataFrame(d).sort_values(by=keys[4])

    @classmethod
    def get_fittings(cls) -> pd.DataFrame:
        """
        Returns an overview of the fittings in the network organised as a Pandas DataFrame.

        """
        keys = [
            'section_id',
            'fitting_id',
            f'dp [{cls.units["pressure"]}]',
            'zeta',
            'zeta_inf',
            'zeta_d',
            'ELR',
            'Kv'
        ]
        d = {k: [] for k in keys}
        for section in cls.network.sections.values():
            if section.fittings:
                for id_, fitting in section.fittings.items():
                    d[keys[0]].append(section.id)
                    d[keys[1]].append(id_)
                    d[keys[2]].append(fitting.pressure_drop(cls.units['pressure'], 3))
                    c = fitting.get_coefficients()
                    d[keys[3]].append(c['zeta'])
                    d[keys[4]].append(c['zeta_inf'])
                    d[keys[5]].append(c['zeta_d'])
                    d[keys[6]].append(c['ELR'])
                    d[keys[7]].append(c['Kv'])
        return pd.DataFrame(d)

    @classmethod
    def get_control_valves(cls) -> pd.DataFrame:
        """
        Get an overview of the control valves in the network organised as a Pandas DataFrame.

        """
        keys = [
            'section_id',
            f'dp [{cls.units["pressure"]}]',
            'Kvs',
            'auth'
        ]
        d = {k: [] for k in keys}
        cv_dict = cls.network.get_control_valves()
        for section_id, tup in cv_dict.items():
            control_valve = tup[0]
            section = tup[1]
            d[keys[0]].append(section_id)
            d[keys[1]].append(control_valve.pressure_drop(cls.units['pressure'], 3))
            d[keys[2]].append(control_valve.Kvs)
            d[keys[3]].append(control_valve.authority(section.pressure_drop))
        return pd.DataFrame(d)

    @classmethod
    def get_balancing_valves(cls) -> pd.DataFrame:
        """
        Returns an overview of the balancing valves in the network organised as a Pandas DataFrame.

        """
        keys = [
            'section_id',
            f'dp [{cls.units["pressure"]}]',
            'Kvr',
            'Kvs'
        ]
        d = {k: [] for k in keys}
        bv_dict = cls.network.get_balancing_valves()
        for section_id, tup in bv_dict.items():
            balancing_valve = tup[0]
            d[keys[0]].append(section_id)
            d[keys[1]].append(balancing_valve.pressure_drop(cls.units['pressure'], 3))
            d[keys[2]].append(round(balancing_valve.Kvr, 3))
            d[keys[3]].append(balancing_valve.Kvs)
        return pd.DataFrame(d)
