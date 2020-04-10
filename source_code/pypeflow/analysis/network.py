"""
## Modeling the components for network flow analysis
"""
from typing import Dict, Tuple, Optional, List, Type
import math
import threading
import quantities as qty
from pypeflow.core.fluids import Fluid
from pypeflow.core.pipe_schedules import PipeSchedule
from pypeflow.core.pipe import Pipe


class Node:
    """Class that models a network node."""

    def __init__(self, id_: str):
        """Create a Node with given id (*str*)."""
        self.id: str = id_
        self._in: Dict[str, Section] = {}
        self._out: Dict[str, Section] = {}

    def connect(self, section: 'Section', direction: str):
        """
        Connect a pipe section (*Section* object) to the node.

        Parameter `direction` (*str*) needs to specify if the section leaves the node (value = *'out'*) or arrives at
        the node (value = *'in'*).
        """
        if direction == 'in':
            self._in.setdefault(section.id, section)  # only add section if key section.id does not exist
        if direction == 'out' and section not in self._out:
            self._out.setdefault(section.id, section)

    def check_flow_balance(self, V_ext_in: Optional[List[qty.VolumeFlowRate]] = None,
                           V_ext_out: Optional[List[qty.VolumeFlowRate]] = None) -> float:
        """
        Check if the sum of entering and exiting flow rates at the network node equals zero (see physical law of the
        conservation of mass).

        **Parameters:**

        - `V_ext_in`: (list of *quantities.VolumeFlowRate* objects) = external flow rates that enter the network at
        the node
        - `V_ext_out`: (list of *quantities.VolumeFlowRate* objects) = flow rates that leave the network at the node

        **Returns:** (*float*) = the difference between entering and exiting flow rates at the node

        """
        sum_V_in = sum([section.V for section in self._in.values() if section.type != 'pseudo'])
        sum_V_out = sum([section.V for section in self._out.values() if section.type != 'pseudo'])
        if V_ext_in is not None:
            sum_V_in += sum([V() for V in V_ext_in])
        if V_ext_out is not None:
            sum_V_out += sum([V() for V in V_ext_out])
        return sum_V_in - sum_V_out

    @property
    def incoming(self) -> List['Section']:
        """Get a list of the *Section* objects that are entering the node."""
        return list(self._in.values())

    @property
    def outgoing(self) -> List['Section']:
        """Get a list of the *Section* objects that are leaving the node."""
        return list(self._out.values())


class Section:
    """Class that models a pipe section in a network."""

    def __init__(self, section_id: str, loop_id: str, start_node: Node, end_node: Node):
        """
        Create *Section* object.

        **Parameters:**

        - `section_id`: (*str*) = id of the pipe section in the network
        - `loop_id`: (*str*) = id of the primary network loop to which the section belongs
        - `start_node`: (*Node* object) = start node of the pipe section
        - `end_node`: (*Node* object) = end node of the pipe section

        """
        self.id: str = section_id
        self.loop_id: str = loop_id
        self.start_node: Node = start_node
        self.end_node: Node = end_node
        self.start_node.connect(self, 'out')
        self.end_node.connect(self, 'in')
        self.type: str = ''
        self.sign: int = 1
        self._length: float = math.nan
        self._nom_diameter: float = math.nan
        self.zeta: float = math.nan
        self._a: Tuple[float, float, float] = (math.nan, math.nan, math.nan)
        self.V: float = math.nan
        self.dp: float = math.nan
        self._fluid: Optional[Fluid] = None
        self._pipe_schedule: Optional[Type[PipeSchedule]] = None

    def configure_section(self, **kwargs):
        """
        Configure the pipe section.

        **kwargs:**

        - `dp_fixed`: (*quantities.Pressure*) = pressure difference between start and end node in case of a pseudo
        section
        - `pump_curve`: (*Tuple[float, float, float]*) = pump coefficients that describe the pump curve in case of a
        pump section
        - `length`: (*quantities.Length*) = the length of the section
        - `nominal_diameter`: (*quantities.Length*) = the nominal diameter of the section
        - `zeta`: (*float*) = sum of resistance coefficients of fittings/valves in the section
        - `flow_rate`: (*quantities.VolumeFlowRate*) = (initial guess of) the flow rate through the section
        - `fluid`: (object of type *pyflow.core.fluids.Fluid*) = fluid that flows in the section
        - `pipe_schedule`: (type of *pyflow.core.pipe_schedules.PipeSchedule*) = pipe schedule of the section

        """
        if kwargs['dp_fixed'] is not None:
            self.type = 'pseudo'
            self.dp = kwargs['dp_fixed']()
        else:
            if kwargs['pump_curve'] is not None:
                self.type = 'pump'
                self._a = kwargs['pump_curve']
            else:
                self.type = 'pipe'
            self._length = kwargs['length']()
            self._nom_diameter = kwargs['nominal_diameter']()
            self.zeta = kwargs['zeta']
            V = kwargs['flow_rate']()
            if V < 0.0:
                self.V = abs(V)
                self.sign = -1
            else:
                self.V = V
            self._fluid = kwargs['fluid']
            self._pipe_schedule = kwargs['pipe_schedule']

    @property
    def dp_pipe(self) -> float:
        """Get (signed) pressure drop (*float*) [Pa] across the pipe section."""
        return self.sign * self.dp

    @property
    def n_pipe(self) -> float:
        """Get numerator term of pipe section to calculate the loop correction term."""
        return 2.0 * self.dp / self.V

    @property
    def dp_pump(self) -> float:
        """Get (signed) pressure drop or gain (*float*) across the pump section."""
        return (self.sign * self.dp
                - self.sign * (self._a[0] + self._a[1] * self.V + self._a[2] * self.V ** 2))

    @property
    def n_pump(self) -> float:
        """Get numerator term of pump section to calculate loop correction term."""
        return (2.0 * self.dp / self.V
                - (self._a[1] + 2.0 * self._a[2] * self.V))

    @property
    def dp_pseudo(self) -> float:
        """Get pressure difference (*float*) across the pseudo section."""
        return self.dp

    def calc_pressure_drop(self):
        """Calculate pressure drop across the pipe or pump section."""
        if self.type != 'pseudo':
            pipe = Pipe.create(
                fluid=self._fluid,
                pipe_schedule=self._pipe_schedule,
                length=self.length,
                flow_rate=self.flow_rate,
                nominal_diameter=self.nominal_diameter,
                sum_zeta=self.zeta
            )
            self.dp = pipe.friction_loss() + pipe.minor_losses()

    @property
    def length(self) -> qty.Length:
        """Get length (*quantities.Length*) of the section."""
        return qty.Length(self._length)

    @property
    def nominal_diameter(self) -> qty.Length:
        """Get diameter (*quantities.Length*) of the section."""
        return qty.Length(self._nom_diameter)

    @property
    def flow_rate(self) -> qty.VolumeFlowRate:
        """Get flow rate (*quantities.VolumeFlowRate*) of the section."""
        return qty.VolumeFlowRate(self.V)

    @property
    def pressure_drop(self) -> qty.Pressure:
        """Get pressure drop (or gain in case of a pump section) (*quantities.Pressure*) across the section."""
        dp = 0.0
        if self.type == 'pipe':
            dp = self.dp_pipe
        elif self.type == 'pump':
            dp = self.dp_pump
        elif self.type == 'pseudo':
            dp = self.dp_pseudo
        return qty.Pressure(dp)

    @property
    def velocity(self) -> qty.Velocity:
        """Get flow velocity (*quantities.Velocity*) in the section."""
        if self.type != 'pseudo':
            di = self._pipe_schedule.inside_diameter(self.nominal_diameter)
        else:
            di = qty.Length(math.nan)
        return qty.Velocity(self.V / (math.pi * di() ** 2 / 4.0))

    @property
    def velocity_pressure(self) -> qty.Pressure:
        """Get velocity pressure (*quantities.Velocity*) in the section."""
        v = self.velocity()
        rho = self._fluid.density()
        return qty.Pressure(rho * v ** 2 / 2)


class Loop:
    """Class that models a primary loop in the network."""

    def __init__(self, id_: str):
        """Create *Loop* object with given id (*str*)."""
        self.id: str = id_
        self.sections: Dict[str, Section] = {}
        self.corr_term: float = math.nan

    def add_section(self, section: Section):
        """Add a section (*Section* object) to the loop."""
        v = self.sections.setdefault(section.id, section)
        if v is not section:
            raise ValueError(f'section with {section.id} was already added to loop {self.id}')

    def calculate_correction_term(self):
        """Calculate loop correction term."""
        d = 0.0
        n = 0.0
        for section in self.sections.values():
            section.calc_pressure_drop()
            if section.type == 'pipe':
                d += section.dp_pipe
                n += section.n_pipe
            elif section.type == 'pump':
                d += section.dp_pump
                n += section.n_pump
            elif section.type == 'pseudo':
                d += section.dp_pseudo
        self.corr_term = d / n

    @property
    def pressure_drop(self):
        """Get pressure drop (*float*) around the loop."""
        dp_loop = 0.0
        for section in self.sections.values():
            if section.type == 'pipe':
                dp_loop += section.dp_pipe
            elif section.type == 'pump':
                dp_loop += section.dp_pump
            elif section.type == 'pseudo':
                dp_loop += section.dp_pseudo
        return dp_loop


class FlowPath(List[Section]):
    """Class that models a flow path between the start and end node of the network."""

    def __repr__(self):
        return '|'.join([section.id for section in self])

    def get_first_real_section(self) -> Section:
        """Get the first section in the flow path that is not a pseudo section."""
        for section in self:
            if section.type != 'pseudo':
                return section

    def get_last_real_section(self) -> Section:
        """Get the last section in the flow path that is not a pseudo section."""
        for section in reversed(self):
            if section.type != 'pseudo':
                return section

    @property
    def dynamic_head(self) -> qty.Pressure:
        """Get the dynamic head (*quantities.Pressure*) between end and start node of the flow path."""
        return qty.Pressure(sum([section.pressure_drop() for section in self if section.type != 'pseudo']))

    @property
    def elevation_head(self) -> qty.Pressure:
        """Get the elevation head (*quantities.Pressure*) between end and start node of the flow path."""
        return qty.Pressure(sum([section.pressure_drop() for section in self if section.type == 'pseudo']))

    @property
    def velocity_head(self) -> qty.Pressure:
        """Get the velocity head (*quantities.Pressure*) between end and start node of the flow path."""
        first = self.get_first_real_section()
        last = self.get_last_real_section()
        vp1 = first.velocity_pressure()
        vp2 = last.velocity_pressure()
        return qty.Pressure(vp2 - vp1)

    @property
    def static_head(self) -> qty.Pressure:
        """Get the static head (*quantities.Pressure*) between end and start node of the flow path."""
        dp_vel = self.velocity_head()
        dp_elev = self.elevation_head()
        dp_dyn = self.dynamic_head()
        return qty.Pressure(-(dp_vel + dp_elev + dp_dyn))


class Network:
    """Class that models a piping network."""

    def __init__(self):
        self.start_node_id: str = ''
        self.end_node_id: str = ''
        self.fluid: Optional[Fluid] = None
        self.pipe_schedule: Optional[Type[PipeSchedule]] = None
        self.loops: Dict[str, Loop] = {}
        self.nodes: Dict[str, Node] = {}
        self.sections: Dict[str, List[Section]] = {}
        self._paths: List[FlowPath] = []

    @classmethod
    def create(cls, **kwargs):
        """
        Create Network object.

        **kwargs:**

        - `start_node_id`: (*str*) = start node of the network
        - `end_node_id`: (*str*) = end node of the network
        - `fluid`: (object of type *pyflow.core.fluids.Fluid*) = fluid that flows in the network
        - `pipe_schedule`: (type of *pyflow.core.pipe_schedules.PipeSchedule) = pipe schedule of the network sections

        """
        start_node_id: str = kwargs.get('start_node_id')
        end_node_id: str = kwargs.get('end_node_id')
        fluid: Fluid = kwargs.get('fluid')
        pipe_schedule: Type[PipeSchedule] = kwargs.get('pipe_schedule')

        n = cls()
        n.start_node_id = start_node_id
        n.end_node_id = end_node_id
        n.fluid = fluid
        n.pipe_schedule = pipe_schedule
        return n

    def add_section(self, **kwargs):
        """
        Add a new section to the network.

        **kwargs:**

        - `section_id`: (*str*) = id of the section
        - `start_node_id`: (*str*) = the id of the start node of the section
        - `end_node_id`: (*str*) = the id of the end node of the section
        - `loop_id`: (*str*) = the id of the loop to which the section belongs

        """
        section_id = kwargs.pop('section_id')
        sn_id = kwargs.pop('start_node_id')
        en_id = kwargs.pop('end_node_id')
        loop_id = kwargs.pop('loop_id')
        kwargs.update({'fluid': self.fluid, 'pipe_schedule': self.pipe_schedule})

        start_node = self.nodes.setdefault(sn_id, Node(sn_id))
        end_node = self.nodes.setdefault(en_id, Node(en_id))
        section = Section(section_id, loop_id, start_node, end_node)
        section.configure_section(**kwargs)
        loop = self.loops.setdefault(loop_id, Loop(loop_id))
        loop.add_section(section)
        section_list = self.sections.setdefault(section_id, [])
        section_list.append(section)

    def calculate_step(self):
        """
        Calculate new flow rates and pressure drops following the Hardy Cross method.

        """
        # calculate loop correction terms
        for loop in self.loops.values():
            loop.calculate_correction_term()

        # apply correction terms to sections in each loop, except pseudo sections
        for loop in self.loops.values():
            for section in loop.sections.values():
                if section.type != 'pseudo':
                    # check if section belongs to two loops
                    section_list = self.sections[section.id]
                    if len(section_list) == 2:
                        if section_list[0].loop_id != loop.id:
                            second_loop_id = section_list[0].loop_id
                        else:
                            second_loop_id = section_list[1].loop_id
                        corr_term = loop.corr_term - self.loops[second_loop_id].corr_term
                    else:
                        corr_term = loop.corr_term
                    # apply correction term to section flow rate
                    if section.sign == -1:
                        section.V += corr_term
                    else:
                        section.V -= corr_term
                    # if the flow rate direction is reversed after correction, reverse sign
                    if section.V < 0.0:
                        section.sign = -section.sign
                        section.V = abs(section.V)

    def _check_loops(self, error: float):
        """Check if the loop pressure drops are smaller than the allowable error (i.e. deviation from zero)."""
        if False in [abs(loop.pressure_drop) < error for loop in self.loops.values()]:
            return False
        return True

    def solve(self, error: float = 1.0e-3, i_max: int = 30):
        """
        Solve the piping network for flow rates and pressure drops.

        **Parameters:**

        - `error`: (*float*) = allowable deviation from zero for the pressure drop around each loop
        - `i_max`: (*int*) = the maximum number of iterations to find a solution within the given error tolerance

        If no solution within the given fault tolerance is found after maximum number of iterations an *OverflowError*
        exception is raised.

        """
        i = 0
        self.calculate_step()
        while not self._check_loops(error):
            self.calculate_step()
            i += 1
            if i > i_max:
                raise OverflowError('no solution found while maximum number of iterations has been exceeded')
        return True

    def _find_flow_paths(self):
        """Find all the possible flow paths between the start node and end node of the network."""
        path = FlowPath()
        self._paths.append(path)
        try:
            node = self.nodes[self.start_node_id]  # get start node of network
            self._search(node, path)               # begin searching at start node of network
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
        while node.id != self.end_node_id:
            if len(node.outgoing) > 1:
                for section in node.outgoing[1:]:
                    new_path = FlowPath()
                    new_path.extend(path)
                    new_path.append(section)
                    self._paths.append(new_path)
                    thread = threading.Thread(
                        target=self._search,
                        args=(self.nodes[section.end_node.id], new_path)
                    )
                    thread.start()
                    thread.join()
            path.append(node.outgoing[0])
            node = self.nodes[path[-1].end_node.id]

    @property
    def paths(self) -> List[FlowPath]:
        """Get the flow paths (*List[FlowPath]*) in the network."""
        if not self._paths: self._find_flow_paths()
        return self._paths

    @property
    def flow_rate(self) -> qty.VolumeFlowRate:
        """
        Get the flow rate (*quantities.VolumeFlowRate*) of the network, i.e. the sum of the leaving flow rates at the
        start node of the network, which is equal to the total flow rate that enters the network.

        """
        start_node = self.nodes[self.start_node_id]
        V = 0.0
        for section in start_node.outgoing:
            V += section.flow_rate()
        return qty.VolumeFlowRate(V)
