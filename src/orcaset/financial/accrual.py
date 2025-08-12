from datetime import date
from typing import Callable
from dataclasses import dataclass, field

from .period import Period
from .yearfrac import YF


@dataclass(slots=True)
class Accrual:
    """
    An accrual over a period of time with an associated function to calculate partial period accruals.

    Args:
        period: The period of time over which the accrual is calculated.
        value: The value of the accrual for the period.
        yf: A function that takes two dates and returns the fraction of a year between them.
    """

    period: Period
    _f: Callable[[], float] = field(repr=False)
    yf: Callable[[date, date], float] | YF._Actual360 | YF._CMonthly | YF._Thirty360 = field(repr=False)
    _value: float = None  # type: ignore

    def __init__(
        self,
        period: Period,
        value: float | Callable[[], float],
        yf: Callable[[date, date], float] | YF._Actual360 | YF._CMonthly | YF._Thirty360,
    ):
        object.__setattr__(self, "period", period)
        if isinstance(value, (float, int)):
            object.__setattr__(self, "_f", lambda: value)
            object.__setattr__(self, "_value", value)
        else:
            object.__setattr__(self, "_f", value)
        object.__setattr__(self, "yf", yf)

    @property
    def value(self) -> float:
        value = getattr(self, "_value", None)
        if value is None:
            value = self._f()
            setattr(self, "_value", value)
        return value

    @classmethod
    def act360(cls, period: Period, value: float) -> "Accrual":
        """Create an accrual using the actual/360 day count convention as the yf."""
        return cls(period, value, YF.actual360)

    @classmethod
    def cmonthly(cls, period: Period, value: float) -> "Accrual":
        """Create an accrual using the calendar monthly day count convention as the yf."""
        return cls(period, value, YF.cmonthly)

    def split_at(self, split_date: date) -> tuple["Accrual", "Accrual"]:
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

        first_value = self.value * (first_fraction / total_fraction)
        second_value = self.value * (second_fraction / total_fraction)

        return (
            Accrual(Period(self.period.start, split_date), first_value, self.yf),
            Accrual(Period(split_date, self.period.end), second_value, self.yf),
        )

    def __add__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(
                period=self.period,
                value=self.value + other,
                yf=self.yf,
            )
        raise TypeError(f"Unsupported operand type(s) for +: 'Accrual' and '{type(other).__name__}'")

    def __radd__(self, other: float | int):
        return self.__add__(other)

    def __sub__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(
                period=self.period,
                value=self.value - other,
                yf=self.yf,
            )
        raise TypeError(f"Unsupported operand type(s) for -: 'Accrual' and '{type(other).__name__}'")

    def __rsub__(self, other: float | int):
        return self.__add__(other)

    def __mul__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(
                period=self.period,
                value=self.value * other,
                yf=self.yf,
            )
        raise TypeError(f"Unsupported operand type(s) for *: 'Accrual' and '{type(other).__name__}'")

    def __rmul__(self, other: float | int):
        return self.__mul__(other)

    def __truediv__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Accrual(
                period=self.period,
                value=self.value / other,
                yf=self.yf,
            )
        raise TypeError(f"Unsupported operand type(s) for /: 'Accrual' and '{type(other).__name__}'")

    def __neg__(self):
        return Accrual(
            period=self.period,
            value=-self.value,
            yf=self.yf,
        )
