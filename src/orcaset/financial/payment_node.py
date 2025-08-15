import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import takewhile
from typing import Callable, Iterable, Iterator

from orcaset import Node, cached_generator


class Payment:
    """
    Represents a payment made on a specific date.

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
            return Payment(date=self.date, value=lambda: self.value + other)
        raise TypeError(f"Cannot add {type(other)} to {type(self)}. Only float or int is allowed.")

    def __radd__(self, other: float | int):
        return self.__add__(other)

    def __sub__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Payment(date=self.date, value=lambda: self.value - other)
        raise TypeError(f"Cannot subtract {type(other)} from {type(self)}. Only float or int is allowed.")

    def __mul__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Payment(date=self.date, value=lambda: self.value * other)
        raise TypeError(f"Cannot multiply {type(other)} with {type(self)}. Only float or int is allowed.")

    def __rmul__(self, other: float | int):
        return self.__mul__(other)

    def __truediv__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Payment(date=self.date, value=lambda: self.value / other)
        raise TypeError(f"Cannot divide {type(self)} by {type(other)}. Only float or int is allowed.")

    def __neg__(self):
        return Payment(date=self.date, value=lambda: -self.value)
    
    def __repr__(self) -> str:
        return f"Payment(date={self.date}, value={self._value.__repr__() if self._value is not None else '<unevaluated>'})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Payment):
            return NotImplemented
        return self.date == other.date and self.value == other.value


def _combine_payment_series(
    first: Iterable[Payment], second: Iterable[Payment], operator: Callable[[float, float], float]
) -> Iterable[Payment]:
    """
    Combine two payment series using the provided operator.
    Payments on the same date are combined using the operator.
    """
    first = iter(first)
    second = iter(second)

    first_pmt = next(first, None)
    second_pmt = next(second, None)
    while first_pmt is not None or second_pmt is not None:
        if first_pmt is None:
            yield second_pmt  # type: ignore
            second_pmt = next(second, None)
        elif second_pmt is None:
            yield first_pmt
            first_pmt = next(first, None)
        elif first_pmt.date < second_pmt.date:
            yield first_pmt
            first_pmt = next(first, None)
        elif first_pmt.date > second_pmt.date:
            yield second_pmt
            second_pmt = next(second, None)
        else:
            yield Payment(date=first_pmt.date, value=lambda fp=first_pmt, sp=second_pmt: operator(fp.value, sp.value))
            first_pmt = next(first, None)
            second_pmt = next(second, None)


@dataclass
class PaymentSeriesBase[P](Node[P], ABC):
    """A series of `Payment` objects. Subclasses must override `_payments` to provide consecutive values by ascending date."""

    @abstractmethod
    def _payments(self) -> Iterable[Payment]: ...

    @cached_generator
    def __iter__(self) -> Iterator[Payment]:
        yield from self._payments()

    def on(self, dt: datetime.date) -> float:
        """
        Get the payment at a given date. Returns zero if no payment on the given date.
        """
        pmt = next((pmt for pmt in self if pmt.date == dt), None)
        if pmt is None:
            return 0
        else:
            return pmt.value

    def over(self, from_date: datetime.date, to_date: datetime.date) -> float:
        """
        Get the total payment from and excluding `from_date` to and including `to_date`.
        Returns zero if no payments are made in the period.
        """
        total = 0
        for pmt in takewhile(lambda pmt: pmt.date <= to_date, self):
            if from_date < pmt.date <= to_date:
                total += pmt.value
        return total

    def after(self, dt: datetime.date) -> "PaymentSeries":
        """Get a new `PaymentSeries` containing payments after the given date."""
        return PaymentSeries(payment_series=(pmt for pmt in self if pmt.date > dt))

    def __add__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        if isinstance(other, PaymentSeriesBase):
            return PaymentSeries(payment_series=_combine_payment_series(self, other, lambda a, b: a + b))
        elif isinstance(other, (float, int)):
            return PaymentSeries(payment_series=(pmt + other for pmt in self))
        else:
            raise TypeError(f"Cannot add {type(other)} to {type(self)}. Only PaymentSeriesBase, float or int is allowed.")

    def __radd__(self, other: "PaymentSeriesBase | float | int"):
        return self.__add__(other)

    def __sub__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        if isinstance(other, PaymentSeriesBase):
            return PaymentSeries(payment_series=_combine_payment_series(self, other, lambda a, b: a - b))
        elif isinstance(other, (float, int)):
            return PaymentSeries(payment_series=(pmt - other for pmt in self))
        else:
            raise TypeError(f"Cannot subtract {type(other)} from {type(self)}. Only PaymentSeriesBase, float or int is allowed.")

    def __mul__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        if isinstance(other, PaymentSeriesBase):
            return PaymentSeries(payment_series=_combine_payment_series(self, other, lambda a, b: a * b))
        elif isinstance(other, (float, int)):
            return PaymentSeries(payment_series=(pmt * other for pmt in self))
        else:
            raise TypeError(f"Cannot multiply {type(other)} with {type(self)}. Only PaymentSeriesBase, float or int is allowed.")

    def __rmul__(self, other: "PaymentSeriesBase | float | int"):
        return self.__mul__(other)

    def __truediv__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        if isinstance(other, PaymentSeriesBase):
            return PaymentSeries(payment_series=_combine_payment_series(self, other, lambda a, b: a / b))
        elif isinstance(other, (float, int)):
            return PaymentSeries(payment_series=(pmt / other for pmt in self))
        else:
            raise TypeError(f"Cannot divide {type(self)} by {type(other)}. Only PaymentSeriesBase, float or int is allowed.")

    def __neg__(self) -> "PaymentSeries":
        """Return a new PaymentSeries that negates the payments of `self`"""
        return PaymentSeries(payment_series=(-pmt for pmt in self))


@dataclass
class PaymentSeries[P](PaymentSeriesBase[P]):
    """A series of payments that takes a `payment_series: Iterable[Pmt]` constructor variable."""

    payment_series: Iterable[Payment]

    def _payments(self) -> Iterable[Payment]:
        yield from self.payment_series
