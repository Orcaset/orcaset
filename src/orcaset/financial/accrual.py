from datetime import date
from typing import Callable

from .period import Period
from .yearfrac import YF, YfType


class Accrual:
    """
    An accrual over a period of time with an associated function to calculate partial period accruals.

    Pass a zero argument function as the value to delay evaluation.
    Accessing the value property or comparing equality will force the evaluation of the function.

    Args:
        period: The period of time over which the accrual is calculated.
        value: The value of the accrual for the period.
        yf: A function that takes two dates and returns the fraction of a year between them.
    """

    def __init__(
        self,
        period: Period,
        value: float | Callable[[], float],
        yf: YfType,
    ):
        self.period = period
        self.yf = yf

        if isinstance(value, (float, int)):
            self._f: Callable[[], float] = lambda: value
            self._value = value
        else:
            self._f: Callable[[], float] = value
            self._value = None

    @property
    def value(self) -> float:
        value = self._value
        if value is None:
            value = self._f()
            self._value = value
        return value

    @classmethod
    def act360(cls, period: Period, value: float | Callable[[], float]) -> "Accrual":
        """Create an accrual using the actual/360 day count convention as the yf."""
        return cls(period, value, YF.actual360)

    @classmethod
    def cmonthly(cls, period: Period, value: float | Callable[[], float]) -> "Accrual":
        """Create an accrual using the calendar monthly day count convention as the yf."""
        return cls(period, value, YF.cmonthly)

    @classmethod
    def thirty360(cls, period: Period, value: float | Callable[[], float]) -> "Accrual":
        """Create an accrual using the 30/360 day count convention as the yf."""
        return cls(period, value, YF.thirty360)

    def split(self, split_date: date) -> tuple["Accrual", "Accrual"]:
        """
        Split an accrual at a given date, proportionally allocating the value.

        Args:
            split_date: The date at which to split the accrual. Must be greater than the start date and less than the end date of the accrual period.
        """
        if not (self.period.start < split_date < self.period.end):
            raise ValueError(f"Split date {split_date} must be within the accrual period {self.period}")

        total_fraction = self.yf(self.period.start, self.period.end)
        first_fraction = self.yf(self.period.start, split_date)
        second_fraction = self.yf(split_date, self.period.end)

        first_frac = first_fraction / total_fraction
        second_frac = second_fraction / total_fraction

        return (
            Accrual(Period(self.period.start, split_date), lambda: self.value * first_frac, self.yf),
            Accrual(Period(split_date, self.period.end), lambda: self.value * second_frac, self.yf),
        )

    def __add__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(period=self.period, value=lambda: self.value + other, yf=self.yf)
        raise TypeError(f"Unsupported operand type(s) for +: 'Accrual' and '{type(other).__name__}'")

    def __radd__(self, other: float | int):
        return self.__add__(other)

    def __sub__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(period=self.period, value=lambda: self.value - other, yf=self.yf)
        raise TypeError(f"Unsupported operand type(s) for -: 'Accrual' and '{type(other).__name__}'")

    def __mul__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(period=self.period, value=lambda: self.value * other, yf=self.yf)
        raise TypeError(f"Unsupported operand type(s) for *: 'Accrual' and '{type(other).__name__}'")

    def __rmul__(self, other: float | int):
        return self.__mul__(other)

    def __truediv__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(period=self.period, value=lambda: self.value / other, yf=self.yf)
        raise TypeError(f"Unsupported operand type(s) for /: 'Accrual' and '{type(other).__name__}'")

    def __neg__(self):
        return Accrual(period=self.period, value=lambda: -self.value, yf=self.yf)
    
    def __repr__(self) -> str:
        return f"Accrual(period={self.period.__repr__()}, value={self._value if self._value else '() -> float'}, yf={self.yf.__repr__()})"
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Accrual):
            return NotImplemented
        return (
            self.period == value.period
            and self.value == value.value
            and self.yf == value.yf
        )
