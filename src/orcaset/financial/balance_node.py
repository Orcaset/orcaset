import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator

from orcaset import Node, cached_generator, merge_distinct


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
        return f"Balance(date={self.date}, value={self._value if self._value else '() -> float'})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Balance):
            return NotImplemented
        return self.date == other.date and self.value == other.value


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

    def rebase(self, dates: Iterable[datetime.date]) -> Iterable[Balance]:
        """
        Rebase the balance series to include balances on dates in `dates`.

        Pads with zero balances if `dates` extends outside the range of `self._balances`.
        """
        distinct_dates = merge_distinct((p.date for p in self), dates)
        balances = (Balance(date=dt, value=self.at(dt)) for dt in distinct_dates)
        return BalanceSeries(balance_series=balances)

    def after(self, dt: datetime.date) -> "BalanceSeries":
        """Return a new `BalanceSeries` from and including `dt`. Interpolates the balance at `dt` if it does not exist."""
        return BalanceSeries(balance_series=(bal for bal in self if bal.date > dt))

    def __add__(self, other: "BalanceSeriesBase") -> "BalanceSeries":
        if not isinstance(other, BalanceSeriesBase):
            raise TypeError(f"Cannot add {type(other)} to {type(self)}")

        def create_merged_balances(iter_first, iter_second) -> Iterable[Balance]:
            next_first = next(iter_first, None)
            next_second = next(iter_second, None)
            last_first = None
            last_second = None

            while next_first is not None or next_second is not None:
                # If one iterator is exhausted, yield from the other
                if next_first is None:
                    yield next_second  # type: ignore
                    last_second = next_second
                    next_second = next(iter_second, None)
                elif next_second is None:
                    yield next_first
                    last_first = next_first
                    next_first = next(iter_first, None)
                # Both iterators have values, compare dates
                elif next_first.date < next_second.date:
                    yield Balance(
                        date=next_first.date, value=next_first.value + last_second.value if last_second else 0
                    )
                    last_first = next_first
                    next_first = next(iter_first, None)
                elif next_first.date > next_second.date:
                    yield Balance(
                        date=next_second.date, value=next_second.value + last_first.value if last_first else 0
                    )
                    last_second = next_second
                    next_second = next(iter_second, None)
                else:  # Dates are equal, sum values
                    yield Balance(date=next_first.date, value=next_first.value + next_second.value)
                    last_first = next_first
                    last_second = next_second
                    next_first = next(iter_first, None)
                    next_second = next(iter_second, None)

        return BalanceSeries(balance_series=create_merged_balances(iter(self), iter(other)))

    def __neg__(self) -> "BalanceSeries":
        """Return a new BalanceSeries that negates the balances of `self`"""
        return BalanceSeries(balance_series=(-bal for bal in self))


@dataclass
class BalanceSeries[P](BalanceSeriesBase[P]):
    """A series of balances that takes a `balance_series: Iterable[Balance]` constructor value."""

    balance_series: Iterable[Balance]

    def _balances(self) -> Iterable[Balance]:
        yield from self.balance_series
