from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from itertools import tee
from typing import Iterable, Iterator, TypeVar, overload

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
            first, second = self.current_accrual.split_at(period.end)
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

        return AccrualSeries(accrual_series=_RebasedAccrualIterator(self, unified_periods))

    @overload
    def __add__(self, other: "AccrualSeriesBase") -> "AccrualSeriesBase": ...
    @overload
    def __add__(self, other: int | float) -> 'AccrualSeriesBase': ...
    def __add__(self, other: "AccrualSeriesBase | int | float") -> "AccrualSeriesBase":
        # Return a new AccrualSeries that lazily adds the accruals of `self` and `other`
        # Periods iterate over the set of unique dates in both series
        if isinstance(other, AccrualSeriesBase) or isinstance(other, _AddAccrualSeries):
            return AccrualSeries(_AddAccrualSeries(first_series=self, second_series=other))
        elif isinstance(other, (int, float)):
            # If other is a number, add it to each accrual's value
            return AccrualSeries(accrual_series=(Accrual(a.period, a.value + other, a.yf) for a in self))

        return NotImplemented

    @overload
    def __radd__(self, other: "AccrualSeriesBase") -> "AccrualSeriesBase": ...
    @overload
    def __radd__(self, other: int | float) -> 'AccrualSeriesBase': ...
    def __radd__(self, other: "AccrualSeriesBase | int | float"):
        return self.__add__(other)

    def __neg__(self) -> "AccrualSeries":
        """Return a new AccrualSeries that negates the accruals of `self`"""
        return AccrualSeries(accrual_series=(-a for a in self))
    
    def __mul__(self, other) -> "AccrualSeries":
        if isinstance(other, (int, float)):
            return AccrualSeries(acc * other for acc in self)
        return NotImplemented
    
    def __rmul__(self, other) -> "AccrualSeries":
        return self.__mul__(other)

    def after(self, dt: date) -> "AccrualSeries":
        """Get a new `AccrualSeries` containing accruals after the given date. Interpolates a partial accrual starting at `dt`."""
        return AccrualSeries(accrual_series=(a for a in self.rebase([Period(dt, dt)]) if a.period.start >= dt))

    def override_accruals(self, accruals: Iterable[Accrual]) -> "AccrualSeries":
        """
        Create a new `AccrualSeries` overriding values in the original accrual series.
        """
        rebased = self.rebase((a.period for a in accruals))

        def new_accruals():
            rebased_iter = tee(rebased, 1)[0]
            override_iter = tee(accruals, 1)[0]
            curr_override_accrual = next(override_iter, None)
            next_accrual = None

            for a in rebased_iter:
                if curr_override_accrual and (
                    a.period.start >= curr_override_accrual.period.start
                    and a.period.end <= curr_override_accrual.period.end
                ):
                    next_accrual = curr_override_accrual
                    continue

                if next_accrual and next_accrual == curr_override_accrual:
                    yield next_accrual
                    curr_override_accrual = next(override_iter, None)

                yield a

        return AccrualSeries(accrual_series=new_accruals())

    def accrue(self, dt1: date, dt2: date) -> float:
        """Calculate the total accrued value of a series between two dates."""
        accrual_iter = iter(self)
        accrual = next(accrual_iter, None)
        accrued_value = 0.0

        while accrual is not None and accrual.period.start < dt2:
            if accrual.period.end <= dt1:
                accrual = next(accrual_iter, None)
                continue

            # Use Accrual.split_at to handle splitting accruals
            if accrual.period.start < dt1:
                accrual = accrual.split_at(dt1)[1]

            if accrual.period.end > dt2:
                accrual = accrual.split_at(dt2)[0]

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

            # Use Accrual.split_at to handle splitting accruals
            if accrual.period.start < dt1:
                accrual = accrual.split_at(dt1)[1]

            if accrual.period.end > dt2:
                accrual = accrual.split_at(dt2)[0]

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

    accrual_series: A

    def _accruals(self) -> Iterable[Accrual]:
        yield from self.accrual_series


def _rebase_accruals(accruals: Iterable[Accrual], periods: Iterable[Period]) -> _RebasedAccrualIterator:
    """
    Rebase the accrual iterable to a new set of periods.

    This method will split existing accruals at the boundaries of the new periods
    and the original accrual periods. The resulting iterable will contain accruals
    for all unique, contiguous periods from both sources.

    Any (partial) periods that do not overlap with any existing accruals will be filled with `0.0`.

    Returns a generator that yield the new `Accrual`s.
    """
    # Get the combined set of unique periods using merged_periods
    unified_periods = merged_periods((a.period for a in iter(accruals)), iter(periods))
    return _RebasedAccrualIterator(accruals, unified_periods)


@dataclass(kw_only=True)
class _AddAccrualSeries:
    """Object representing the addition of two `AccrualSeries` objects."""

    first_series: AccrualSeriesBase
    second_series: "AccrualSeriesBase  | _AddAccrualSeries"

    @cached_generator
    def __iter__(self) -> Iterator[Accrual]:
        yield from self._accruals()

    def _accruals(self) -> Iterable[Accrual]:
        periods = merged_periods(
            (a.period for a in iter(self.first_series)),
            (a.period for a in iter(self.second_series)),
        )

        # create independent iterators for the periods
        periods, first_periods, second_periods = tee(periods, 3)

        rebased_first = self.first_series.rebase(first_periods)
        rebased_second = _rebase_accruals(self.second_series, second_periods)

        new_accruals = (
            Accrual(p, first_accrual.value + second_accrual.value, first_accrual.yf)
            for p, first_accrual, second_accrual in zip(periods, rebased_first, rebased_second)
        )

        yield from new_accruals
