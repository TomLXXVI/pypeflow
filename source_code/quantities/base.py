from typing import Dict, Optional, Union


class Quantity:
    base_unit: str = ""
    units: Dict[str, float] = {}

    @classmethod
    def convert(cls, src_value: float, src_unit: str, des_unit: str) -> float:
        """Convert a quantity value from one unit to another unit.

        src_value : float
            the value to convert
        src_unit : str
            the current unit in which the quantity value is expressed
        des_unit : str
            the new unit in which the quantity value is to be expressed

        return value : float
            the value of the quantity expressed in the new unit
        """
        src_cf = cls.units.get(src_unit)  # get conversion factor to go from source unit to base unit
        base_value = src_value / src_cf   # convert source value to value expressed in base unit
        des_cf = cls.units.get(des_unit)  # get conversion factor to go from base unit to destination unit
        des_value = base_value * des_cf   # convert value in base unit to value in destination unit
        return des_value

    def __init__(self, value: float = None, unit: str = None):
        """Create Quantity object.

        value: float
            value of quantity
        unit: str
            unit of quantity (default is the base unit of the quantity)
        """
        if unit is None: unit = self.base_unit
        # internally the quantity value is stored being expressed in the base unit of the quantity
        self.base_unit_value: Union[float, None] = None
        if value is not None:
            self.base_unit_value = self.convert(value, src_unit=unit, des_unit=self.base_unit)
        # favourite or default unit to be used for the quantity
        self.default_unit: str = self.base_unit

    def __call__(self, unit: str = None, decimal_places: int = None) -> Optional[float]:
        """Get quantity value in the unit asked. If `decimal_places` is set to an integer value, the returned value
        is rounded to that number of digits after the decimal point. If no unit is passed, the value will be returned
        expressed in its base unit. If unit is set to 'default', the value returned will be expressed in the default
        unit.
        """
        if unit is None: unit = self.base_unit
        if unit == 'default': unit = self.default_unit
        if self.base_unit_value is not None:
            raw_value = self.convert(self.base_unit_value, src_unit=self.base_unit, des_unit=unit)
            if decimal_places is not None:
                return float(f"{raw_value:.{decimal_places}f}")
            else:
                return raw_value
        return None

    def __repr__(self) -> str:
        """Return string representation of Quantity object expressed in its favourite or default unit."""
        if self.base_unit_value is not None:
            val = self.convert(self.base_unit_value, src_unit=self.base_unit, des_unit=self.default_unit)
        else:
            val = 'empty'
        return f"({val}, {self.default_unit})"

    def get(self, unit: str = None, decimal_places: int = None) -> Optional[float]:
        """Analog to internal method __call__"""
        return self.__call__(unit, decimal_places)
