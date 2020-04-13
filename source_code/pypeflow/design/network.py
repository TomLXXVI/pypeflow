"""
## Modeling the components for piping network design
"""
from typing import List, Dict, Optional, Tuple, Type
import threading
import math
import quantities as qty
from pypeflow.core import Pipe, Fitting, BalancingValve, ControlValve
from pypeflow.core.pipe_schedules import PipeSchedule
from pypeflow.core.fluids import Fluid
from pypeflow.core.pump import Pump
from pypeflow.core.resistance_coefficient import ResistanceCoefficient


class Section:
    """Class that models a pipe section in a network."""

    def __init__(self):
        self._id: str = ''
        self._start_node: Node = Node()
        self._end_node: Node = Node()
        self._pipe: Pipe = Pipe()
        self._fittings: Dict[str, Fitting] = {}
        self._balancing_valve: Optional[BalancingValve] = None
        self._control_valve: Optional[ControlValve] = None
        self._pump: Optional[Pump] = None
        self._real: bool = False

    @classmethod
    def create_pseudo(cls, **kwargs):
        """
        Create a pseudo section.<br>
        A pseudo section is to be used in open networks (eg. drinking water installations) to make a closing connection
        to the end node of the network. This is needed so that the program can find the flow paths in the network.
        A flow path is any sequence of sections that connects the start node of the network with the end node of the
        network.
        Between the start node and end node of the network the feed pressure is present that establish the flow in the
        network.

        **kwargs:**

        - `id`: (*str*) = id of the section in the network
        - `start_node_id`: (*str*) = id of the start node of the section
        - `end_node_id`: (*str*) = id of the exit node of the section
        - `start_node_height`: (*quantities.Length*) = height of the start node with respect to a chosen reference plane
        - `end_node_height`: (*quantities.Length*) = height of the end node with respect to a chosen reference plane

        """
        id_: str = kwargs.get('id')
        sn_id: str = kwargs.get('start_node_id')
        en_id: str = kwargs.get('end_node_id')
        sn_h: qty.Length = kwargs.get('start_node_height')
        en_h: qty.Length = kwargs.get('end_node_height')

        s = cls()
        s._id = id_
        s._start_node = Node.create(sn_id, sn_h)
        s._end_node = Node.create(en_id, en_h)
        return s

    @classmethod
    def create_real(cls, **kwargs):
        """
        Create a real pipe section.

        **kwargs:**

        - `id`: (*str*) = id of the section in the network
        - `start_node_id`: (*str*) = id of the start node of the section
        - `end_node_id`: (*str*) = id of the exit node of the section
        - `start_node_height`: (*quantities.Length*) = height of the start node with respect to a chosen reference plane
        - `end_node_height`: (*quantities.Length*) = height of the end node with respect to a chosen reference plane
        - `fluid`: (object of type *pyflow.core.fluids.Fluid*) = fluid that flows in the section
        - `pipe_schedule`: (type of *pyflow.core.pipe_schedules.PipeSchedule*) = pipe schedule of the section
        - `length`: (*quantities.Length*) = length of the section
        - `nominal_diameter`: (*quantities.Length*) = nominal diameter of the section
        - `flow_rate`: (*quantities.VolumeFlowRate*) = flow rate through the section
        - `pressure_drop`: (*quantities.Pressure*) = pressure drop due to friction across the section

        If flow rate and friction loss are set -> diameter will be calculated<br>
        If flow rate and nominal diameter are set -> friction loss will be calculated

        """
        s = cls.create_pseudo(**kwargs)
        s._real = True

        fluid: Fluid = kwargs.get('fluid')
        pipe_schedule: Type[PipeSchedule] = kwargs.get('pipe_schedule')
        l: qty.Length = kwargs.get('length')
        dn: Optional[qty.Length] = kwargs.get('nominal_diameter')
        V: Optional[qty.VolumeFlowRate] = kwargs.get('flow_rate')
        dp: Optional[qty.Pressure] = kwargs.get('pressure_drop')

        if (V is not None) and (dp is not None):  # diameter unknown
            s._pipe = Pipe.create(fluid, pipe_schedule, l, flow_rate=V, friction_loss=dp)
        if (V is not None) and (dn is not None):  # pressure drop unknown
            s._pipe = Pipe.create(fluid, pipe_schedule, l, flow_rate=V, nominal_diameter=dn)
        return s

    def add_fitting(self, **kwargs):
        """
        Add a fitting/valve to the section.

        **kwargs:**

        - `id`: (*str*) = id of the fitting/valve
        - `type`: (*str*) = a description of the type of fitting/valve
        - `zeta`: (*float*) = (1st) resistance coefficient of the fitting
        - `zeta_inf`: (*float*) = 2nd resistance coefficient of the fitting (see 3K-method)
        - `zeta_d`: (*float*) = 3th resistance coefficient of the fitting (see 3K-method)
        - `ELR`: (*float*) = equivalent length ratio of the fitting (see Crane-K-method)
        - `Kv`: (*float*) = flow coefficient of the fitting/valve

        Based on the parameters that are set, the pressure drop across the fitting/valve is calculated using the
        appropriate method (see pyflow.core.fitting.Fitting).

        """
        id_: str = kwargs.get('id')
        type_: str = kwargs.get('type')
        zeta: float = kwargs.get('zeta', math.nan)
        zeta_inf: float = kwargs.get('zeta_inf', math.nan)
        zeta_d: float = kwargs.get('zeta_d', math.nan)
        ELR: float = kwargs.get('ELR', math.nan)
        Kv: float = kwargs.get('Kv', math.nan)

        if not math.isnan(Kv):
            f = Fitting.create_w_flow_rate(type_, self._pipe.fluid, self._pipe.flow_rate, Kv)
        else:
            f = Fitting.create_w_velocity(type_, self._pipe.fluid, self._pipe.velocity,
                                          self._pipe.cross_section.diameter,
                                          zeta=zeta, zeta_inf=zeta_inf, zeta_d=zeta_d, ELR=ELR)
        v = self._fittings.setdefault(id_, f)
        if v is not f: raise ValueError(f'a fitting with {id_} was already added to the section')

    def add_balancing_valve(self, dp_100: qty.Pressure) -> float:
        """
        Add a balancing valve to the section. A section can have only one balancing valve.

        **Parameter:**

        - `dp_100` (*quantities.Pressure*) = pressure drop across fully open valve.

        **Returns:** (*float*)<br>
        Preliminary calculated Kvs value for the balancing valve.

        """
        self._balancing_valve = BalancingValve.create(
            self._pipe.fluid,
            self._pipe.flow_rate,
            dp_100
        )
        return self._balancing_valve.Kvs

    def init_balancing_valve(self, Kvs: float):
        """
        Set commercial available Kvs value (*float*) for the balancing valve.
        """
        self._balancing_valve.Kvs = Kvs

    def set_balancing_valve(self, dp_excess: qty.Pressure) -> float:
        """
        Determine the calculated Kvr setting (*float*) of the balancing valve in order to dissipate the excess
        feed pressure (*quantities.Pressure*).

        **Returns:** (*float*) The Kvr setting for the balancing valve.

        """
        self._balancing_valve.set_pressure_excess(dp_excess)
        return self._balancing_valve.Kvr

    def add_control_valve(self, target_authority: float, dp_crit_path: qty.Pressure) -> float:
        """
        Add a control valve to the section. A section can have only one control valve.

        **Parameter:**

        - `target_authority`: (*float*) = the valve authority aimed at

        **Returns:** (*float*) Preliminary Kvs value for the control valve.

        """
        self._control_valve = ControlValve.create(
            self._pipe.fluid,
            self._pipe.flow_rate,
            target_authority,
            dp_crit_path
        )
        return self._control_valve.Kvs

    def set_control_valve(self, Kvs: float):
        """Set commercial available Kvs value (*float*) for the control valve."""
        self._control_valve.Kvs = Kvs

    def add_pump(self, pump_coefficients: Tuple[float, float, float]):
        """
        Add a pump to the section.

        Parameter `coefficients` is a tuple of 3 *float* values which are the coefficients of the pump curve described
        by the equation: dp_pump = `coefficients[0]` + `coefficients[1]` * V + `coefficients[2]` * V **2.

        """
        self._pump = Pump.create(*pump_coefficients)

    @property
    def id(self) -> str:
        """Get id of the section."""
        return self._id

    @property
    def start_node(self) -> 'Node':
        """Get start node (*Node*) of the section."""
        return self._start_node

    @property
    def end_node(self) -> 'Node':
        """Get end node (*Node*) of the section."""
        return self._end_node

    @property
    def pipe(self) -> Pipe:
        """Get the straight pipe (*pyflow.core.pipe.Pipe*) of the section."""
        return self._pipe

    @property
    def fittings(self) -> Dict[str, Fitting]:
        """
        Get a dictionary with the fittings in the section. Keys are the fitting ids (*str*) and values the
        *Fitting* objects (*pyflow.core.fitting.Fitting*).

        """
        return self._fittings

    @property
    def balancing_valve(self) -> BalancingValve:
        """Get the balancing valve (*pyflow.core.valves.BalancingValve*) in the section."""
        return self._balancing_valve

    @property
    def control_valve(self) -> ControlValve:
        """Get the control valve (*pyflow.core.valves.ControlValve*) in the section."""
        return self._control_valve

    @property
    def pressure_drop(self) -> qty.Pressure:
        """Get the pressure drop (*quantities.Pressure*) across the section."""
        dp = self._pipe.friction_loss()
        dp += sum([fitting.pressure_drop() for fitting in self._fittings.values()])
        if self._balancing_valve is not None:
            dp += self._balancing_valve.pressure_drop()
        if self._pump is not None:
            dp -= self._pump.added_head(self._pipe.flow_rate)()
        if self._control_valve is not None:
            dp += self._control_valve.pressure_drop()
        return qty.Pressure(dp)

    @property
    def real(self) -> bool:
        """Returns *True* if the section is not a pseudo section."""
        if self._real:
            return True
        return False

    @property
    def flow_rate(self) -> qty.VolumeFlowRate:
        """Get the flow rate (*quantities.VolumeFlowRate*) in the section."""
        return self._pipe.flow_rate

    @property
    def zeta(self) -> float:
        """Get the global resistance coefficient of all fittings, balancing valve and control valve in the section."""
        zeta = 0.0
        for fitting in self._fittings.values():
            zeta += fitting.zeta
        if self._balancing_valve is not None:
            if not math.isnan(self._balancing_valve.Kvr):
                zeta_bal = ResistanceCoefficient.from_Kv(
                    self._balancing_valve.Kvr,
                    self._pipe.cross_section.diameter
                )
            else:
                zeta_bal = ResistanceCoefficient.from_Kv(
                    self._balancing_valve.Kvs,
                    self._pipe.cross_section.diameter
                )
            zeta += zeta_bal
        if self._control_valve is not None:
            zeta_ctrl = ResistanceCoefficient.from_Kv(
                self._control_valve.Kvs,
                self._pipe.cross_section.diameter
            )
            zeta += zeta_ctrl
        return zeta

    @property
    def length(self) -> qty.Length:
        """Get the length (*quantities.Length*) of the section."""
        return self._pipe.length

    @property
    def nominal_diameter(self) -> qty.Length:
        """Get the nominal diameter (*quantities.Length*) of the section pipe."""
        return self._pipe.cross_section.nominal_diameter

    @property
    def pump(self) -> Pump:
        """Get the pump (*pyflow.core.pump.Pump*) in the section."""
        return self._pump


class Node:
    """Class that models a network node."""

    def __init__(self):
        self._id: str = ''
        self._height: float = 0.0
        self._in: List[Section] = []
        self._out: List[Section] = []

    @classmethod
    def create(cls, id_: str, height: qty.Length = qty.Length(0.0)) -> 'Node':
        """
        Create network node.

        **Parameters:**

        - `id_`: (*str*) = the id of the node
        - height: (*quantities.Length*) = height of the node with respect to a reference plane

        **Returns:** (*Node*)

        """
        n = cls()
        n.id = id_
        n.height = height
        return n

    @property
    def id(self) -> str:
        """Get/set id (*str*) of the node."""
        return self._id

    @id.setter
    def id(self, id_: str):
        self._id = id_

    @property
    def height(self) -> qty.Length:
        """Get/set the height (*quantities.Length*) of the node with respect to a reference plane."""
        return qty.Length(self._height)

    @height.setter
    def height(self, h: qty.Length):
        self._height = h()

    def connect(self, section: Section, direction: str):
        """
        Connect a section with the node.

        **Parameters:**

        - `section`: (*Section*) = the section to connect with the node
        - `direction`: (*str*) = the flow sense in the section: into the node (value = *'in'*) or out of the node
        (value = *'out'*)

        """
        if direction.lower() == 'in' and section not in self._in:
            self._in.append(section)
        if direction.lower() == 'out' and section not in self._out:
            self._out.append(section)

    @property
    def incoming(self) -> List[Section]:
        """
        Get a list of the sections that arrive at the node (flow sense into the node).
        """
        return self._in

    @property
    def outgoing(self) -> List[Section]:
        """
        Get a list of the sections that leave the node (flow sense out of the node).
        """
        return self._out


class FlowPath(List[Section]):
    """
    Class that models a flow path in the network.

    A flow path is a list of sections. It starts at the start node of the network and ends in the end node of the
    network.
    """

    def __repr__(self):
        return '|'.join([section.id for section in self])

    def get_first_real_section(self) -> Section:
        """Get the first section (*Section* object) of the path that is not a pseudo section."""
        for section in self:
            if section.real:
                return section

    def get_last_real_section(self) -> Section:
        """Get the last section (*Section* object) of the path that is not a pseudo section."""
        for section in reversed(self):
            if section.real:
                return section

    @property
    def dynamic_head(self) -> qty.Pressure:
        """
        Get the dynamic head (*quantities.Pressure*) between the end node of the last real section and the start node
        of first real section in the path. (Any pseudo sections in the path are ignored.)
        """
        return qty.Pressure(sum([section.pressure_drop() for section in self if section.real]))

    @property
    def height(self) -> qty.Length:
        """
        Get the height difference (*quantities.Length*) between the end node of the last real section and the start node
        of first real section in the path. (Any pseudo sections in the path are ignored.)
        """
        first = self.get_first_real_section()
        last = self.get_last_real_section()
        z1 = first.start_node.height()
        z2 = last.end_node.height()
        return qty.Length(z2 - z1)

    @property
    def elevation_head(self) -> qty.Pressure:
        """
        Get the elevation head (*quantities.Pressure*) between the end node of the last real section and the start node
        of first real section in the path. (Any pseudo sections in the path are ignored.)
        """
        dh = self.height()
        return qty.Pressure(dh, 'm')

    @property
    def velocity_head(self) -> qty.Pressure:
        """
        Get the velocity head (*quantities.Pressure*) between the end node of the last real section and the start node
        of first real section in the path. (Any pseudo sections in the path are ignored.)
        """
        first = self.get_first_real_section()
        last = self.get_last_real_section()
        vp1 = first.pipe.velocity_pressure()
        vp2 = last.pipe.velocity_pressure()
        return qty.Pressure(vp2 - vp1)

    @property
    def static_head_required(self) -> qty.Pressure:
        """
        Get the static head (*quantities.Pressure*) between the end node of the last real section and the start node
        of first real section in the path. (Any pseudo sections in the path are ignored.)
        This is the pressure difference that must be applied between the end node of the path and its start node in
        order to establish the desired flow rates along the path. However, note that flow paths must also be balanced
        to accomplish the design flow rates in each section of the network.
        """
        dp_vel = self.velocity_head()
        dp_elev = self.elevation_head()
        dp_dyn = self.dynamic_head()
        return qty.Pressure(dp_vel + dp_elev + dp_dyn)


class Network:
    """Class that models a piping network."""

    def __init__(self):
        self._start_node_id: str = ''
        self._end_node_id: str = ''
        self._fluid: Optional[Fluid] = None
        self._pipe_schedule: Optional[Type[PipeSchedule]] = None
        self._nodes: Dict[str, Node] = {}
        self._sections: Dict[str, Section] = {}
        self._paths: List[FlowPath] = []

    @classmethod
    def create(cls, **kwargs):
        """
        Create *Network* object.

        **kwargs:**

        - `start_node_id`: (*str*) = id of the start node of the network
        - `end_node_id`: (*str*) = id of the end node of the network
        - `fluid`: (object of type *pyflow.core.fluids.Fluid*) = fluid that flows in the network
        - `pipe_schedule`: (type of *pyflow.core.pipe_schedules.PipeSchedule*) = pipe schedule of the sections in the
        network

        """
        sn_id: str = kwargs.get('start_node_id')
        en_id: str = kwargs.get('end_node_id')
        fluid: Fluid = kwargs.get('fluid')
        pipe_schedule: Type[PipeSchedule] = kwargs.get('pipe_schedule')

        n = cls()
        n._start_node_id = sn_id
        n._end_node_id = en_id
        n._fluid = fluid
        n._pipe_schedule = pipe_schedule
        return n

    def add_section(self, **kwargs):
        """
        Add a section to the network.

        **kwargs:**

        - `id`: (*str*) = id of the section in the network
        - `start_node_id`: (*str*) = id of the start node of the section
        - `end_node_id`: (*str*) = id of the exit node of the section
        - `start_node_height`: (*quantities.Length*) = height of the start node with respect to a chosen reference plane
        - `end_node_height`: (*quantities.Length*) = height of the end node with respect to a chosen reference plane
        - `length`: (*quantities.Length*) = length of the section
        - `nominal_diameter`: (*quantities.Length*) = nominal diameter of the section
        - `flow_rate`: (*quantities.VolumeFlowRate*) = flow rate through the section
        - `pressure_drop`: (*quantities.Pressure*) = pressure drop due to friction across the section

        """
        kwargs.update(fluid=self._fluid, pipe_schedule=self._pipe_schedule)
        if kwargs['flow_rate'] is not None:
            section = Section.create_real(**kwargs)
        else:
            section = Section.create_pseudo(**kwargs)
        v = self._sections.setdefault(section.id, section)
        if v is not section:
            raise ValueError(f'a section with {section.id} was already added to the network')
        else:
            sn = self._nodes.setdefault(section.start_node.id, section.start_node)
            sn.connect(section, 'out')
            en = self._nodes.setdefault(section.end_node.id, section.end_node)
            en.connect(section, 'in')

    @property
    def sections(self) -> Dict[str, Section]:
        """Get a dictionary with the sections in the network. Keys: section ids, values: *Section* objects."""
        return self._sections

    def _find_flow_paths(self):
        """Find all the possible flow paths between the start node and end node of the network."""
        path = FlowPath()
        self._paths.append(path)
        try:
            node = self._nodes[self._start_node_id]  # get start node of network
            self._search(node, path)                 # begin searching at start node of network
        except IndexError:
            self._paths = []

    def _search(self, node: Node, path: FlowPath):
        # search until the end node of the network has been reached
        # if the current node has more than 1 outgoing connection, then
        # for each outgoing connection except the first one...
        #   create a new empty path
        #   add the current path to the new path
        #   add the connection to the new path
        #   add the new path to the list of paths in the network
        #   create a thread that begins searching from the end node of the connection
        # add the first outgoing connection of the current node to the current path
        # and then set current node to the end node of the first outgoing connection
        while node.id != self._end_node_id:
            if len(node.outgoing) > 1:
                for section in node.outgoing[1:]:
                    new_path = FlowPath()
                    new_path.extend(path)
                    new_path.append(section)
                    self._paths.append(new_path)
                    thread = threading.Thread(
                        target=self._search,
                        args=(self._nodes[section.end_node.id], new_path)
                    )
                    thread.start()
                    thread.join()
            path.append(node.outgoing[0])
            node = self._nodes[path[-1].end_node.id]

    @property
    def paths(self) -> List[FlowPath]:
        """Get a list of the flow paths (object *FlowPath*) in the network."""
        if not self._paths: self._find_flow_paths()
        return self._paths

    @property
    def critical_path(self) -> FlowPath:
        """Get the critical path (object *FlowPath*) in the network."""
        static_head_max = 0.0
        idx = 0
        for i in range(len(self.paths)):
            static_head = (self._paths[i].velocity_head() + self._paths[i].elevation_head()
                           + self._paths[i].dynamic_head())
            if static_head > static_head_max:
                static_head_max = static_head
                idx = i
        return self._paths[idx]

    def get_balancing_valves(self) -> Dict[str, Tuple[BalancingValve, FlowPath]]:
        """
        Get the balancing valves in the network.

        **Returns:**<br>
        A dictionary whose keys are ids of sections that have a balancing valve.
        The values of the dictionary are tuples containing the *BalancingValve* object and the *FlowPath* object in
        which the balancing valve is present.

        """
        d = {}
        for path in self.paths:
            for section in path:
                if section.balancing_valve:
                    d[section.id] = (section.balancing_valve, path)
        return d

    def get_control_valves(self) -> Dict[str, Tuple[ControlValve, Section]]:
        """
        Get the control valves in the network.

        **Returns:**<br>
        A dictionary whose keys are ids of sections that have a control valve.
        The values of the dictionary are tuples containing the *ControlValve* object and the *Section* object in
        which the control valve is present.

        """
        d = {}
        for section in self._sections.values():
            if section.control_valve:
                d[section.id] = (section.control_valve, section)
        return d

    @property
    def start_node_id(self) -> str:
        """Get the start node id of the network."""
        return self._start_node_id

    @property
    def end_node_id(self) -> str:
        """Get the end node id of the network."""
        return self._end_node_id

    @property
    def flow_rate(self) -> qty.VolumeFlowRate:
        """Get the flow rate (*quantities.VolumeFlowRate*) that enters the network."""
        start_node = self._nodes[self._start_node_id]
        V = 0.0
        for section in start_node.outgoing:
            V += section.flow_rate()
        return qty.VolumeFlowRate(V)

    @property
    def feed_pressure(self) -> qty.Pressure:
        """
        Get the required feed pressure (*quantities.Pressure*) for the network, i.e. the required static head for
        the critical path in the network. If the network is balanced, all flow paths share the same required static
        head.
        """
        return self.critical_path.static_head_required

    @ property
    def hydraulic_resistance(self) -> float:
        """
        Get the hydraulic resistance (*float*) of the network. Its value is based on flow rate and pressure expressed in
        their base SI-units (m^3/s and Pa).
        """
        V = self.flow_rate()
        dp_feed = self.feed_pressure()
        R = dp_feed / V ** 2
        return R
