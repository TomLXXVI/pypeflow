"""
## Classes that define the cross section of a pipe or duct.
"""
from typing import Optional, Type
import math
import quantities as qty
from pypeflow.core.pipe_schedules import PipeSchedule


class CrossSection:
    """
    Base class from which different shapes of cross sections are derived.
    """

    @property
    def area(self) -> qty.Area:
        """
        Get the area (*quantities.Area*) of the cross section.

        """
        return qty.Area()

    @property
    def diameter(self) -> qty.Length:
        """
        Get/set the (equivalent) diameter (*quantities.Length*) of the cross section.

        """
        return qty.Length()

    @diameter.setter
    def diameter(self, di_th: qty.Length):
        pass


class Circular(CrossSection):
    """Class that models a circular cross section."""

    def __init__(self):
        self._di: float = math.nan       # inside diameter that corresponds with nominal diameter
        self._dn: float = math.nan       # nominal diameter according to pipe schedule
        self._di_th: float = math.nan    # theoretical or calculated inside diameter
        self._pipe_schedule: Optional[Type[PipeSchedule]] = None

    @classmethod
    def create(cls, pipe_schedule: Type[PipeSchedule], dn: Optional[qty.Length] = None,
               di_th: Optional[qty.Length] = None):
        """
        Create a circular cross section.
        To create the cross section, either the nominal diameter or a calculated, theoretical diameter must be passed
        to the method.

        **Parameters:**

        - `pipe_schedule` : *type of core.pipe_schedules.PipeSchedule*<br>
        The pipe schedule that defines the dimensions of the pipe's cross section.
        - `dn` : object of *quantities.Length* (optional, default None)<br>
        The nominal diameter of the cross section that belongs to the pipe schedule being used.
        - `di_th` : object of *quantities.Length* (optional, default None)<br>
        The calculated or theoretical inside diameter of the cross section.

        """
        c = cls()
        c.pipe_schedule = pipe_schedule
        if dn is not None:
            c.nominal_diameter = dn
        elif di_th is not None:
            c.diameter = di_th
        return c

    @property
    def nominal_diameter(self) -> qty.Length:
        """
        Get/set the nominal diameter (*quantities.Length*) of the cross section.

        The inside diameter that corresponds with the nominal diameter is also set based on the pipe schedule that
        was passed at the instance the CrossSection object was created.

        """
        return qty.Length(self._dn)

    @nominal_diameter.setter
    def nominal_diameter(self, dn: qty.Length):
        self._dn = dn()
        # when nominal diameter is set, the corresponding inside diameter is also set
        self._di = self._di_th = self._pipe_schedule.inside_diameter(DN=dn).get()

    @property
    def area(self) -> qty.Area:
        """
        Get the area of the cross section.

        **Returns:**

        - object of *quantities.Area*

        """
        return qty.Area(math.pi * self._di ** 2.0 / 4.0)

    @property
    def diameter(self) -> qty.Length:
        """
        Get/set the inside diameter (*quantities.Length) of the cross section.

        This will also set the nearest nominal diameter and corresponding inside diameter based on the pipe schedule
        that was passed when creating the cross section.

        """
        return qty.Length(self._di)

    @diameter.setter
    def diameter(self, di_th: qty.Length):
        self._di_th = di_th()
        # get the nearest nominal diameter
        dn = self._pipe_schedule.nominal_diameter(d_int=di_th)
        self._dn = dn()
        # get the inside diameter that corresponds with the nominal diameter
        self._di = self._pipe_schedule.inside_diameter(dn).get()

    @property
    def calculated_diameter(self) -> qty.Length:
        """
        Get the calculated or theoretical inside diameter (*quantities.Length*) of the cross section.

        """
        return qty.Length(self._di_th)

    @property
    def pipe_schedule(self) -> Type[PipeSchedule]:
        """
        Get/set the pipe schedule (*core.pipe_schedules.PipeSchedule*) of the cross section.

        """
        return self._pipe_schedule

    @pipe_schedule.setter
    def pipe_schedule(self, schedule: Type[PipeSchedule]):
        self._pipe_schedule = schedule
