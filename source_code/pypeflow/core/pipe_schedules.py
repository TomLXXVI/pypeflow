"""
## Definitions of pipe schedules (dimensional pipe data and pipe wall roughness)
"""
from typing import Optional, Dict, Type
import pandas as pd
import quantities as qty


class PipeSchedule:
    """Base class that implements the user interface for the derived classes."""
    dimensions = None
    pipe_roughness = None

    @classmethod
    def outside_diameter(cls, DN: qty.Length) -> qty.Length:
        """
        Get outside diameter (*quantities.Length*) of pipe with nominal diameter DN (*quantities.Length*).

        """
        DN = int(DN('mm'))
        return qty.Length(cls.dimensions.loc[DN, 'd_ext'], 'mm')

    @classmethod
    def wall_thickness(cls, DN: qty.Length) -> qty.Length:
        """
        Get wall thickness (*quantities.Length*) of pipe with nominal diameter DN (*quantities.Length*).

        """
        DN = int(DN('mm'))
        return qty.Length(cls.dimensions.loc[DN, 't'], 'mm')

    @classmethod
    def inside_diameter(cls, DN: qty.Length) -> qty.Length:
        """
        Get inside diameter (*quantities.Length*) of pipe with nominal diameter DN (*quantities.Length*).

        """
        DN = int(DN('mm'))
        try:
            return qty.Length(cls.dimensions.loc[DN, 'd_int'], 'mm')
        except KeyError:
            return qty.Length(0.0, 'mm')

    @classmethod
    def nominal_diameter(cls, d_int: Optional[qty.Length] = None, d_ext: Optional[qty.Length] = None) -> qty.Length:
        """
        Get nearest nominal diameter when either inside or either outside diameter is given.

        **Parameters:**

        - `d_int`: (*quantities.Length*) = inside diameter (default None).
        - `d_ext`: (*quantities.Length*) = outside diameter (default None).

        **Returns:** (*quantities.Length*)

        """
        if d_int:
            d_int = d_int('mm')
            delta = [abs(d_int - d_int_40) for d_int_40 in cls.dimensions['d_int']]
            idx = delta.index(min(delta))
            return qty.Length(cls.dimensions.index[idx], 'mm')
        elif d_ext:
            d_ext = d_ext('mm')
            delta = [d_ext - d_ext_40 for d_ext_40 in cls.dimensions['d_ext']]
            idx = delta.index(min(delta))
            return qty.Length(cls.dimensions.index[idx], 'mm')


class PipeSchedule40(PipeSchedule):
    """
    Class that holds dimensional data and pipe wall roughness for pipe schedule 40 (ANSI B36.10 - B36.19)
    for carbon and alloy steel + stainless steel.
    """
    d_ext = [10.3, 13.7, 17.1, 21.3, 26.7, 33.4, 42.2, 48.3, 60.3, 73.0, 88.9, 101.6, 114.3]  # [mm]
    t = [1.73, 2.24, 2.31, 2.77, 2.87, 3.38, 3.56, 3.68, 3.91, 5.16, 5.49, 5.74, 6.02]        # [mm]
    d_int = [6.84, 9.22, 12.5, 15.8, 21.0, 26.6, 35.1, 40.9, 52.5, 62.7, 77.9, 90.1, 102.3]   # [mm]
    d_nom = [6, 8, 10, 15, 20, 25, 32, 40, 50, 65, 80, 90, 100]                               # [mm]
    dimensions = pd.DataFrame(
        data={
            'd_ext': d_ext,
            't': t,
            'd_int': d_int
        },
        index=pd.Index(data=d_nom, name='DN')
    )
    pipe_roughness = qty.Length(0.046, 'mm')


class GebMapressSteel(PipeSchedule):
    """
    Class that holds dimensional data and pipe wall roughness for Geberit Mapress C Steel.
    """
    d_ext = [12.0, 15.0, 18.0, 22.0, 28.0, 35.0, 42.0, 54.0, 76.1, 66.7, 88.9, 108.0]  # [mm]
    t = [1.2, 1.2, 1.2, 1.5, 1.5, 1.5, 1.5, 1.5, 2.0, 1.5, 2.0, 2.0]                   # [mm]
    d_int = [d_ext - 2 * t for d_ext, t in zip(d_ext, t)]                              # [mm]
    d_nom = [10, 12, 15, 20, 25, 32, 40, 50, 65, 66.7, 80, 100]                        # [mm]
    dimensions = pd.DataFrame(
        data={
            'd_ext': d_ext,
            't': t,
            'd_int': d_int
        },
        index=pd.Index(data=d_nom, name='DN')
    )
    pipe_roughness = qty.Length(0.010, 'mm')


PIPE_SCHEDULES: Dict[str, Type[PipeSchedule]] = {
    'pipe_schedule_40': PipeSchedule40,
    'geberit_mapress_steel': GebMapressSteel
}
"""Dictionary that holds the available pipe schedules"""
