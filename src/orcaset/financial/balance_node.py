import datetime
import operator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, overload

from orcaset import Node, cached_generator, merge_distinct

from .yearfrac import YfType


class Balance:
    """
    Represents a financial balance at a specific date.

    Pass a zero argument function as the value to lazily delay evaluation.
    Accessing the value property or comparing equality will force the evaluation of the function.
    """

    def __init__(self, date: datetime.date, value: float | Callable[[], float]):
        self.date = date
        if isinstance(value, (float, int)):
            self._f = lambda: value
            self._value = value
        else:
            self._f = value
            self._value = None

    @property
    def value(self) -> float:
        value = self._value
        if value is None:
            value = self._f()
            self._value = value
        return value

    def __add__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=lambda: self.value + other)
        raise TypeError(f"Cannot add {type(other)} to {type(self)}. Use `Balance.__add__` instead.")

    def __radd__(self, other: float | int):
        return self.__add__(other)

    def __sub__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=lambda: self.value - other)
        raise TypeError(f"Cannot subtract {type(other)} from {type(self)}. Use `Balance.__sub__` instead.")

    def __mul__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=lambda: self.value * other)
        raise TypeError(f"Cannot multiply {type(other)} with {type(self)}. Use `Balance.__mul__` instead.")

    def __rmul__(self, other: float | int):
        return self.__mul__(other)

    def __truediv__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=lambda: self.value / other)
        raise TypeError(f"Cannot divide {type(self)} by {type(other)}. Use `Balance.__truediv__` instead.")

    def __neg__(self):
        return Balance(date=self.date, value=lambda: -self.value)

    def __repr__(self) -> str:
        return f"Balance(date={self.date}, value={self._value if self._value else '<unevaluated>'})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Balance):
            return NotImplemented
        return self.date == other.date and self.value == other.value


def _combine_balance_series(iter_first, iter_second, op: Callable[[float, float], float]) -> Iterable[Balance]:
    """
    Merge two balance iterators using the provided operator.

    Args:
        iter_first: First balance iterator
        iter_second: Second balance iterator
        op: Binary operator function (e.g., operator.add, operator.sub)
    """
    next_first = next(iter_first, None)
    next_second = next(iter_second, None)
    last_first = None
    last_second = None

    while next_first is not None or next_second is not None:
        # If one iterator is exhausted, yield last and advance the other
        if next_first is None:
            yield Balance(
                date=next_second.date,  # type: ignore  Both next_first and next_second cannot be None or loop would terminate
                value=lambda ns=next_second, lf=last_first, operation=op: operation(lf.value if lf else 0, ns.value),  # type: ignore
            )
            last_second = next_second
            next_second = next(iter_second, None)
        elif next_second is None:
            yield Balance(
                date=next_first.date,
                value=lambda nf=next_first, ls=last_second, operation=op: operation(nf.value, ls.value if ls else 0),
            )
            last_first = next_first
            next_first = next(iter_first, None)
        # Both iterators have values, compare dates
        elif next_first.date < next_second.date:
            yield Balance(
                date=next_first.date,
                value=lambda nf=next_first, ls=last_second, operation=op: operation(nf.value, ls.value if ls else 0),
            )
            last_first = next_first
            next_first = next(iter_first, None)
        elif next_first.date > next_second.date:
            yield Balance(
                date=next_second.date,
                value=lambda ns=next_second, lf=last_first, operation=op: operation(lf.value if lf else 0, ns.value),
            )
            last_second = next_second
            next_second = next(iter_second, None)
        else:  # Dates are equal, combine values using operator
            yield Balance(
                date=next_first.date,
                value=lambda nf=next_first, ns=next_second, operation=op: operation(nf.value, ns.value),
            )
            last_first = next_first
            last_second = next_second
            next_first = next(iter_first, None)
            next_second = next(iter_second, None)


@dataclass
class BalanceSeriesBase[P](Node[P], ABC):
    """A series of `Balance` objects. Subclasses must override `_balances` to provide consecutive values by ascending date."""

    @abstractmethod
    def _balances(self) -> Iterable["Balance"]: ...

    @cached_generator
    def __iter__(self) -> Iterator[Balance]:
        yield from self._balances()

    def at(self, dt: datetime.date) -> float:
        """Get the balance at a given date. Returns zero balance if date is outside the range of the series."""
        last_balance = 0.0
        for bal in self:
            if bal.date > dt:
                break
            if bal.date == dt:
                return bal.value
            last_balance = bal.value
        return last_balance

    def rebase(self, dates: Iterable[datetime.date]) -> "BalanceSeries[None]":
        """
        Rebase the balance series to include balances on dates in `dates`.

        Pads with zero balances if for any date in `dates` that is before the series starts.
        """
        distinct_dates = merge_distinct((p.date for p in self), dates)
        balances = (Balance(date=dt, value=lambda d=dt: self.at(d)) for dt in distinct_dates)
        return BalanceSeries(series=balances)

    def after(self, dt: datetime.date) -> "BalanceSeries":
        """Return a new `BalanceSeries` from and including `dt`. Interpolates the balance at `dt` if it does not exist."""
        return BalanceSeries(series=(bal for bal in self if bal.date > dt))

    def avg(self, dt1: datetime.date, dt2: datetime.date, yf: YfType) -> float:
        """Return the average balance between two dates. First date must not be after second date."""
        if dt1 >= dt2:
            raise ValueError(f"dt1 {dt1} must be before dt2 {dt2}")

        total_yf = yf(dt1, dt2)
        if total_yf == 0:
            return 0.0

        last_balance = Balance(dt1, self.at(dt1))
        total_balance = 0.0

        for bal in self.after(dt1):
            period_yf = yf(last_balance.date, min(bal.date, dt2))
            total_balance += last_balance.value * period_yf
            last_balance = bal

            if bal.date >= dt2:
                break

        if last_balance.date < dt2:
            total_balance += last_balance.value * yf(last_balance.date, dt2)

        return total_balance / total_yf

    @overload
    def __add__(self, other: float | int) -> "BalanceSeries": ...
    @overload
    def __add__(self, other: "BalanceSeriesBase") -> "BalanceSeries": ...
    def __add__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        if isinstance(other, (float, int)):
            return BalanceSeries(series=(bal + other for bal in self))

        if not isinstance(other, BalanceSeriesBase):
            raise TypeError(f"Cannot add {type(other)} to {type(self)}")

        return BalanceSeries(series=_combine_balance_series(iter(self), iter(other), operator.add))

    @overload
    def __sub__(self, other: float | int) -> "BalanceSeries": ...
    @overload
    def __sub__(self, other: "BalanceSeriesBase") -> "BalanceSeries": ...
    def __sub__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        if isinstance(other, (float, int)):
            return BalanceSeries(series=(bal - other for bal in self))

        if not isinstance(other, BalanceSeriesBase):
            raise TypeError(f"Cannot subtract {type(other)} from {type(self)}")

        return BalanceSeries(series=_combine_balance_series(iter(self), iter(other), operator.sub))

    @overload
    def __mul__(self, other: float | int) -> "BalanceSeries": ...
    @overload
    def __mul__(self, other: "BalanceSeriesBase") -> "BalanceSeries": ...
    def __mul__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        if isinstance(other, (float, int)):
            return BalanceSeries(series=(bal * other for bal in self))

        if not isinstance(other, BalanceSeriesBase):
            raise TypeError(f"Cannot multiply {type(self)} by {type(other)}")

        return BalanceSeries(series=_combine_balance_series(iter(self), iter(other), operator.mul))

    @overload
    def __truediv__(self, other: float | int) -> "BalanceSeries": ...
    @overload
    def __truediv__(self, other: "BalanceSeriesBase") -> "BalanceSeries": ...
    def __truediv__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        if isinstance(other, (float, int)):
            return BalanceSeries(series=(bal / other for bal in self))

        if not isinstance(other, BalanceSeriesBase):
            raise TypeError(f"Cannot divide {type(self)} by {type(other)}")

        return BalanceSeries(series=_combine_balance_series(iter(self), iter(other), operator.truediv))

    def __neg__(self) -> "BalanceSeries":
        """Return a new BalanceSeries that negates the balances of `self`"""
        return BalanceSeries(series=(-bal for bal in self))


@dataclass
class BalanceSeries[P](BalanceSeriesBase[P]):
    """A convenience class for creating a balance series from an `Iterable[Balance]`."""

    series: Iterable[Balance]

    def _balances(self) -> Iterable[Balance]:
        yield from self.series
