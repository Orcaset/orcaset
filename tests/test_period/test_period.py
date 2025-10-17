from datetime import date
from itertools import islice

from dateutil.relativedelta import relativedelta

from src.orcaset.financial.period import Period


def test_period_repr():
    period = Period(date(2021, 1, 1), date(2021, 1, 31))

    assert repr(period) == "Period(2021-01-01, 2021-01-31)"


def test_series_with_date_end():
    start = date(2024, 1, 1)
    freq = relativedelta(months=1)
    end = date(2024, 4, 1)

    periods = list(Period.series(start, freq, end))

    assert periods == [
        Period(date(2024, 1, 1), date(2024, 2, 1)),
        Period(date(2024, 2, 1), date(2024, 3, 1)),
        Period(date(2024, 3, 1), date(2024, 4, 1)),
    ]


def test_series_with_relative_end():
    start = date(2024, 1, 1)
    freq = relativedelta(months=2)
    end = relativedelta(months=6)

    periods = list(Period.series(start, freq, end))

    assert periods == [
        Period(date(2024, 1, 1), date(2024, 3, 1)),
        Period(date(2024, 3, 1), date(2024, 5, 1)),
        Period(date(2024, 5, 1), date(2024, 7, 1)),
    ]


def test_series_without_end_is_unbounded():
    start = date(2024, 1, 1)
    freq = relativedelta(days=7)

    first_three_periods = list(islice(Period.series(start, freq), 3))

    assert first_three_periods == [
        Period(date(2024, 1, 1), date(2024, 1, 8)),
        Period(date(2024, 1, 8), date(2024, 1, 15)),
        Period(date(2024, 1, 15), date(2024, 1, 22)),
    ]
