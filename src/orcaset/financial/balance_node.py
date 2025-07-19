from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Iterator

from orcaset import Node, cached_generator, merge_distinct


@dataclass(frozen=True, slots=True)
class Balance:
    date: date
    value: float

    def __add__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=self.value + other)
        raise TypeError(f"Cannot add {type(other)} to {type(self)}. Use `Balance.__add__` instead.")

    def __radd__(self, other: float | int):
        return self.__add__(other)

    def __sub__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=self.value - other)
        raise TypeError(f"Cannot subtract {type(other)} from {type(self)}. Use `Balance.__sub__` instead.")

    def __rsub__(self, other: float | int):
        return self.__add__(other)

    def __mul__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=self.value * other)
        raise TypeError(f"Cannot multiply {type(other)} with {type(self)}. Use `Balance.__mul__` instead.")

    def __rmul__(self, other: float | int):
        return self.__mul__(other)

    def __truediv__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Balance(date=self.date, value=self.value / other)
        raise TypeError(f"Cannot divide {type(self)} by {type(other)}. Use `Balance.__truediv__` instead.")

    def __neg__(self):
        return Balance(date=self.date, value=-self.value)


@dataclass
class BalanceSeriesBase[P](Node[P], ABC):
    """A series of `Balance` objects. Subclasses must override `_balances` to provide consecutive values by ascending date."""

    @abstractmethod
    def _balances(self) -> Iterable["Balance"]: ...

    @cached_generator
    def __iter__(self) -> Iterator[Balance]:
        yield from self._balances()

    def at(self, dt: date) -> float:
        """Get the balance at a given date. Returns zero balance if date is outside the range of the series."""
        last_balance = None
        for bal in self:
            if bal.date > dt:
                break
            last_balance = bal
        return last_balance.value if last_balance else 0.0

    def rebase(self, dates: Iterable[date]) -> Iterable[Balance]:
        """
        Rebase the balance series to include balances on dates in `dates`.

        Pads with zero balances if `dates` extends outside the range of `self._balances`.
        """
        distinct_dates = merge_distinct((p.date for p in self), dates)
        balances = (Balance(date=dt, value=self.at(dt)) for dt in distinct_dates)
        return BalanceSeries(balance_series=balances)

    def after(self, dt: date) -> "BalanceSeries":
        """Return a new `BalanceSeries` from and including `dt`. Interpolates the balance at `dt` if it does not exist."""
        return BalanceSeries(balance_series=(bal for bal in self.rebase([dt]) if bal.date >= dt))

    def __add__(self, other: "BalanceSeriesBase") -> "BalanceSeries":
        if not isinstance(other, BalanceSeriesBase):
            raise TypeError(f"Cannot add {type(other)} to {type(self)}")

        distinct_dts = merge_distinct((bal.date for bal in self), (bal.date for bal in other))
        summed_balances = (Balance(date=dt, value=self.at(dt) + other.at(dt)) for dt in distinct_dts)
        return BalanceSeries(balance_series=summed_balances)

    def __neg__(self) -> "BalanceSeries":
        """Return a new BalanceSeries that negates the balances of `self`"""
        return BalanceSeries(balance_series=(-bal for bal in self))


@dataclass
class BalanceSeries[P](BalanceSeriesBase[P]):
    """A series of balances that takes a `balance_series: Iterable[Balance]` constructor value."""

    balance_series: Iterable[Balance]

    def _balances(self) -> Iterable[Balance]:
        yield from self.balance_series
