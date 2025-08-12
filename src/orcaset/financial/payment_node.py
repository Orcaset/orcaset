import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import takewhile
from typing import Callable, Iterable, Iterator

from orcaset import Node, cached_generator


@dataclass(slots=True)
class Payment:
    date: datetime.date
    _f: Callable[[], float] = field(repr=False)
    _value: float = None  # type: ignore

    def __init__(self, date: datetime.date, value: float | Callable[[], float]):
        object.__setattr__(self, "date", date)
        if isinstance(value, (float, int)):
            object.__setattr__(self, "_f", lambda: value)
            object.__setattr__(self, "_value", value)
        else:
            object.__setattr__(self, "_f", value)

    @property
    def value(self) -> float:
        value = getattr(self, "_value", None)
        if value is None:
            value = self._f()
            setattr(self, "_value", value)
        return value

    def __add__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Payment(date=self.date, value=self.value + other)
        raise TypeError(f"Cannot add {type(other)} to {type(self)}. Only float or int is allowed.")

    def __radd__(self, other: float | int):
        return self.__add__(other)

    def __sub__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Payment(date=self.date, value=self.value - other)
        raise TypeError(f"Cannot subtract {type(other)} from {type(self)}. Only float or int is allowed.")

    def __rsub__(self, other: float | int):
        return self.__add__(other)

    def __mul__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Payment(date=self.date, value=self.value * other)
        raise TypeError(f"Cannot multiply {type(other)} with {type(self)}. Only float or int is allowed.")

    def __rmul__(self, other: float | int):
        return self.__mul__(other)

    def __truediv__(self, other: float | int):
        if isinstance(other, (float, int)):
            return Payment(date=self.date, value=self.value / other)
        raise TypeError(f"Cannot divide {type(self)} by {type(other)}. Only float or int is allowed.")

    def __neg__(self):
        return Payment(date=self.date, value=-self.value)


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

    def __add__(self, other: "PaymentSeriesBase") -> "PaymentSeries":
        if not isinstance(other, PaymentSeriesBase):
            raise TypeError(f"Cannot add {type(other)} to {type(self)}")

        def summed_payments(first, second) -> Iterable[Payment]:
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
                    yield Payment(date=first_pmt.date, value=lambda fp=first_pmt, sp=second_pmt: fp.value + sp.value)
                    first_pmt = next(first, None)
                    second_pmt = next(second, None)

        return PaymentSeries(payment_series=summed_payments(self, other))

    def __radd__(self, other: "PaymentSeriesBase"):
        return self.__add__(other)

    def __neg__(self) -> "PaymentSeries":
        """Return a new PaymentSeries that negates the payments of `self`"""
        return PaymentSeries(payment_series=(-pmt for pmt in self))


@dataclass
class PaymentSeries[P](PaymentSeriesBase[P]):
    """A series of payments that takes a `payment_series: Iterable[Pmt]` constructor variable."""

    payment_series: Iterable[Payment]

    def _payments(self) -> Iterable[Payment]:
        yield from self.payment_series
