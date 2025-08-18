from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
import operator
from typing import Iterable, Iterator, overload, Callable

from ..decorators import cached_generator
from ..node import Node
from .accrual import Accrual
from .period import Period, merged_periods
from .yearfrac import YF


class _RebasedAccrualIterator:
    def __init__(self, original_accruals: Iterable[Accrual], periods: Iterable[Period]):
        """
        Expects `periods` must be sorted by date and be the intersection of the original accruals and the new periods
        (i.e. new period in `periods` may span multiple original accruals).
        """
        self.original_accruals = iter(original_accruals)
        self.periods = iter(periods)
        self.current_accrual = next(self.original_accruals, None)

    def __iter__(self):
        return self

    def __next__(self):
        period = next(self.periods)

        # If we've exhausted original accruals or period starts after current accrual ends
        if self.current_accrual is None or period.start >= self.current_accrual.period.end:
            return Accrual(period, 0.0, YF.actual360)

        # If the current period ends before the first accrual starts, return a zero accrual
        if period.end <= self.current_accrual.period.start:
            return Accrual(period, 0.0, self.current_accrual.yf)

        # Expects that `periods` intersects with the original accruals, so if there's overlap the start date must always be the same
        # If the end date is during the current accrual, split the accrual
        if period.end < self.current_accrual.period.end:
            first, second = self.current_accrual.split(period.end)
            self.current_accrual = second
            return first
        else:
            # Otherwise, the end date must be the same as the current accrual so return it and advance
            cf = self.current_accrual
            self.current_accrual = next(self.original_accruals, None)
            return cf


class AccrualSeriesBase[P](Node[P], ABC):
    """A series of `Accrual` objects. Subclasses must override `_accruals` to provide consecutive values by ascending date."""

    @abstractmethod
    def _accruals(self) -> Iterable[Accrual]: ...

    @cached_generator
    def __iter__(self) -> Iterator[Accrual]:
        yield from self._accruals()

    def rebase(self, periods: Iterable[Period]) -> "AccrualSeries":
        """
        Rebase the accrual series to a new set of periods.

        This method will split existing accruals at the boundaries of the new periods
        and the original accrual periods. The resulting `AccrualSeries` will contain accruals
        for all unique, contiguous periods from both sources.

        Any (partial) periods that do not overlap with any existing accruals will be filled with `0.0`.

        Returns a new `AccrualSeries`.
        """
        # Get the combined set of unique periods using merged_periods
        unified_periods = merged_periods((a.period for a in iter(self)), iter(periods))

        return AccrualSeries(series=_RebasedAccrualIterator(self, unified_periods))

    @overload
    def __add__(self, other: int | float) -> "AccrualSeriesBase": ...
    @overload
    def __add__(self, other: "AccrualSeriesBase") -> "AccrualSeriesBase": ...
    def __add__(self, other: "AccrualSeriesBase | int | float") -> "AccrualSeriesBase":
        # Return a new AccrualSeries that lazily adds the accruals of `self` and `other`
        # Periods iterate over the set of unique dates in both series
        if isinstance(other, AccrualSeriesBase):
            return AccrualSeries(_CombinedAccrualSeries(self, other, operator.add))
        elif isinstance(other, (int, float)):
            # If other is a number, add it to each accrual's value
            return AccrualSeries(series=(acc + other for acc in self))
        return NotImplemented

    @overload
    def __radd__(self, other: "AccrualSeriesBase") -> "AccrualSeriesBase": ...
    @overload
    def __radd__(self, other: int | float) -> "AccrualSeriesBase": ...
    def __radd__(self, other: "AccrualSeriesBase | int | float"):
        return self.__add__(other)

    @overload
    def __sub__(self, other: int | float) -> "AccrualSeries": ...
    @overload
    def __sub__(self, other: "AccrualSeriesBase") -> "AccrualSeries": ...
    def __sub__(self, other: "float | int | AccrualSeriesBase") -> "AccrualSeries":
        if isinstance(other, AccrualSeriesBase):
            return AccrualSeries(_CombinedAccrualSeries(self, other, operator.sub))
        elif isinstance(other, (int, float)):
            return AccrualSeries(series=(a - other for a in self))
        return NotImplemented
    
    @overload
    def __mul__(self, other: int | float) -> "AccrualSeries": ...
    @overload
    def __mul__(self, other: "AccrualSeriesBase") -> "AccrualSeries": ...
    def __mul__(self, other: "AccrualSeriesBase | int | float") -> "AccrualSeries":
        if isinstance(other, AccrualSeriesBase):
            return AccrualSeries(_CombinedAccrualSeries(self, other, operator.mul))
        elif isinstance(other, (int, float)):
            return AccrualSeries(series=(a * other for a in self))
        return NotImplemented

    @overload
    def __rmul__(self, other: int | float) -> "AccrualSeries": ...
    @overload
    def __rmul__(self, other: "AccrualSeriesBase") -> "AccrualSeries": ...
    def __rmul__(self, other: "AccrualSeriesBase | int | float"):
        return self.__mul__(other)

    def __neg__(self) -> "AccrualSeries":
        """Return a new AccrualSeries that negates the accruals of `self`"""
        return AccrualSeries(series=(-a for a in self))
    
    @overload
    def __truediv__(self, other: int | float) -> "AccrualSeries": ...
    @overload
    def __truediv__(self, other: "AccrualSeriesBase") -> "AccrualSeries": ...
    def __truediv__(self, other: "AccrualSeriesBase | int | float") -> "AccrualSeries":
        if isinstance(other, AccrualSeriesBase):
            return AccrualSeries(_CombinedAccrualSeries(self, other, operator.truediv))
        elif isinstance(other, (int, float)):
            return AccrualSeries(series=(a / other for a in self))
        return NotImplemented

    def after(self, dt: date) -> "AccrualSeries":
        """Get a new `AccrualSeries` containing accruals after the given date. Interpolates a partial accrual starting at `dt`."""

        def split_series(series: AccrualSeriesBase) -> Iterator[Accrual]:
            for accrual in series:
                if accrual.period.end <= dt:
                    continue
                if accrual.period.start < dt < accrual.period.end:
                    _, second = accrual.split(dt)
                    yield second
                else:
                    yield accrual

        return AccrualSeries(series=split_series(self))

    def accrue(self, dt1: date, dt2: date) -> float:
        """Calculate the total accrued value of a series between two dates."""
        if dt1 == dt2:
            return 0.0
        
        if dt1 > dt2:
            dt1, dt2 = dt2, dt1

        accrual_iter = iter(self)
        accrual = next(accrual_iter, None)
        accrued_value = 0.0

        while accrual is not None and accrual.period.start < dt2:
            if accrual.period.end <= dt1:
                accrual = next(accrual_iter, None)
                continue

            if accrual.period.start < dt1:
                accrual = accrual.split(dt1)[1]

            if accrual.period.end > dt2:
                accrual = accrual.split(dt2)[0]

            accrued_value += accrual.value
            accrual = next(accrual_iter, None)
        return accrued_value

    def w_avg(self, dt1: date, dt2: date) -> float:
        """
        Calculate the weighted average of accrual value between two dates.

        The weights are the year fractions of the accrual periods. Returns 0.0 if no overlap with accruals.
        """
        accrual_iter = iter(self)
        accrual = next(accrual_iter, None)
        total_value = 0.0
        total_weight = 0.0

        while accrual is not None and accrual.period.start < dt2:
            if accrual.period.end <= dt1:
                accrual = next(accrual_iter, None)
                continue

            full_period_value = accrual.value

            if accrual.period.start < dt1:
                accrual = accrual.split(dt1)[1]

            if accrual.period.end > dt2:
                accrual = accrual.split(dt2)[0]

            weight = accrual.yf(accrual.period.start, accrual.period.end)
            total_value += full_period_value * weight
            total_weight += weight
            accrual = next(accrual_iter, None)

        return total_value / total_weight if total_weight != 0 else 0.0


@dataclass
class AccrualSeries[A: Iterable[Accrual], P](AccrualSeriesBase[P]):
    """
    A series of `Accrual` objects that takes a `accrual_series: Iterable[Accrual]` initializer parameter.

    Generic with respect to the type of accrual iterable for (de)serialization purposes.
    The accrual iterable type is taken as the first generic type parameter. Defining the iterable type
    allows the (de)serialization engine to correctly infer how `accrual_series` should be (de)serialized.
    """

    series: A

    def _accruals(self) -> Iterable[Accrual]:
        yield from self.series


@dataclass
class _CombinedAccrualSeries:
    """Object representing the addition of two `AccrualSeries` objects."""

    first_series: AccrualSeriesBase
    second_series: AccrualSeriesBase
    operator: Callable[[float, float], float]

    def _lazy_combine(self, acc1: Accrual | None, acc2: Accrual | None) -> Callable[[], float]:
        """
        Combine two values from two accruals using the specified operator.

        If either accrual is None, its value is treated as 0.0 (e.g. None - acc2 == 0 - acc2.value == -acc2.value)
        """
        return lambda: self.operator(acc1.value if acc1 else 0.0, acc2.value if acc2 else 0.0)

    @cached_generator
    def __iter__(self) -> Iterator[Accrual]:
        yield from self._accruals()

    def _accruals(self) -> Iterable[Accrual]:
        # yield from new_accruals
        first_iter = iter(self.first_series)
        second_iter = iter(self.second_series)

        first_accrual = next(first_iter, None)
        second_accrual = next(second_iter, None)

        while first_accrual is not None or second_accrual is not None:
            # First accrual is exhausted, yield from second
            if first_accrual is None:
                yield Accrual(second_accrual.period, self._lazy_combine(None, second_accrual), second_accrual.yf)  # type: ignore
                second_accrual = next(second_iter, None)
            # Second accrual is exhausted, yield from first
            elif second_accrual is None:
                yield Accrual(first_accrual.period, self._lazy_combine(first_accrual, None), first_accrual.yf)
                first_accrual = next(first_iter, None)
            # First accrual ends before second starts, yield first
            elif first_accrual.period.end <= second_accrual.period.start:
                yield Accrual(first_accrual.period, self._lazy_combine(first_accrual, None), first_accrual.yf)
                first_accrual = next(first_iter, None)
            # Second accrual ends before first starts, yield second
            elif second_accrual.period.end <= first_accrual.period.start:
                yield Accrual(second_accrual.period, self._lazy_combine(None, second_accrual), second_accrual.yf)
                second_accrual = next(second_iter, None)
            # First accrual starts before second (and must end after second starts)
            elif first_accrual.period.start < second_accrual.period.start:
                first_part, first_accrual = first_accrual.split(second_accrual.period.start)
                yield Accrual(first_part.period, self._lazy_combine(first_part, None), first_part.yf)
            # Second accrual starts before first (and must end after first starts)
            elif second_accrual.period.start < first_accrual.period.start:
                second_part, second_accrual = second_accrual.split(first_accrual.period.start)
                yield Accrual(second_part.period, self._lazy_combine(None, second_part), second_part.yf)
            # If this stage is reached, both accruals start at the same time
            # First accrual ends before second
            elif first_accrual.period.end < second_accrual.period.end:
                second_part, second_accrual = second_accrual.split(first_accrual.period.end)
                yf = first_accrual.yf if first_accrual.yf == second_part.yf else YF.na
                yield Accrual(first_accrual.period, self._lazy_combine(first_accrual, second_part), yf)
                first_accrual = next(first_iter, None)
            # Second accrual ends before first
            elif second_accrual.period.end < first_accrual.period.end:
                first_part, first_accrual = first_accrual.split(second_accrual.period.end)
                yf = first_part.yf if first_part.yf == second_accrual.yf else YF.na
                yield Accrual(second_accrual.period, self._lazy_combine(first_part, second_accrual), yf)
                second_accrual = next(second_iter, None)
            # Both end at the same time
            else:
                yf = first_accrual.yf if first_accrual.yf == second_accrual.yf else YF.na
                yield Accrual(first_accrual.period, self._lazy_combine(first_accrual, second_accrual), yf)
                first_accrual = next(first_iter, None)
                second_accrual = next(second_iter, None)
