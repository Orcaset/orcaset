import heapq
from datetime import date
from itertools import chain
from typing import Any, Generator, Iterable, NamedTuple, Self, overload

from dateutil.relativedelta import relativedelta


class Period(NamedTuple):
    start: date
    end: date

    def __repr__(self):
        return f"Period({self.start.isoformat()}, {self.end.isoformat()})"

    @overload
    @classmethod
    def series(cls, start: date, freq: relativedelta, end: date | None = None) -> Generator[Self, Any, None]: ...
    @overload
    @classmethod
    def series(
        cls, start: date, freq: relativedelta, end: relativedelta | None = None
    ) -> Generator[Self, Any, None]: ...
    @classmethod
    def series(
        cls, start: date, freq: relativedelta, end: date | relativedelta | None = None
    ) -> Generator[Self, Any, None]:
        """
        Create a generator of consecutive periods starting from `start`.

        Each period has a duration of `freq`.
        The generator continues until the end date is reached. If no end date is provided, the generator is infinite.

        Args:
            start: Start date of the first period.
            freq: Period duration.
            end: Optional end date or offset to determine the end date of the last period.
        """
        if not end:
            end = date.max
        elif isinstance(end, relativedelta):
            end = start + end
        per_start, per_end = start, min(start + freq, end)
        num = 2

        while per_start < end:
            yield cls(per_start, per_end)
            per_start, per_end = per_end, min(start + freq * num, end)
            num += 1


def merged_periods(first: Iterable[Period], second: Iterable[Period]) -> Iterable[Period]:
    """
    Lazily merge two overlapping iterables of periods into a contiguous iterable of distinct periods.

    Requires that the periods in each iterable are sorted by start date.
    """
    first_dates = chain.from_iterable((start, end) for start, end in iter(first))
    second_dates = chain.from_iterable((start, end) for start, end in iter(second))
    min_heap = heapq.merge(first_dates, second_dates)
    min_heap_iter = iter(min_heap)

    last_date = next(min_heap_iter)
    for next_date in min_heap_iter:
        if next_date != last_date:
            yield Period(last_date, next_date)
            last_date = next_date
