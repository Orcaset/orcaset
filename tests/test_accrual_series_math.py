from datetime import date
from typing import Iterable
from itertools import islice

import pytest
from dateutil.relativedelta import relativedelta

from orcaset.financial import Accrual, AccrualSeriesBase, Period


class InfiniteGrowth[P = None](AccrualSeriesBase[P]):
    def _accruals(self) -> Iterable[Accrual]:
        period = Period(date(2020, 12, 31), date(2021, 12, 31))
        value = 0
        while True:
            yield Accrual.cmonthly(period, value)
            period = Period(period.end, period.end + relativedelta(years=1))


@pytest.fixture
def infinite_series():
    return InfiniteGrowth()


def test_accrual_series_neg(infinite_series):
    neg_series = -infinite_series
    orig_values = list((acc.value for acc in islice(infinite_series, 10)))
    neg_values = list((acc.value for acc in islice(neg_series, 10)))
    assert neg_values == [-v for v in orig_values]


def test_accrual_series_add(infinite_series):
    plus_one = infinite_series + 1
    orig_values = list((acc.value for acc in islice(infinite_series, 10)))
    plus_one_values = list((acc.value for acc in islice(plus_one, 10)))
    assert plus_one_values == [v + 1 for v in orig_values]

    plus_acc_series = infinite_series + infinite_series
    plus_acc_values = list((acc.value for acc in islice(plus_acc_series, 10)))
    assert plus_acc_values == [v + v for v in orig_values]


def test_accrual_series_radd(infinite_series):
    plus_one = 1 + infinite_series
    orig_values = list((acc.value for acc in islice(infinite_series, 10)))
    plus_one_values = list((acc.value for acc in islice(plus_one, 10)))
    assert plus_one_values == [v + 1 for v in orig_values]


def test_accrual_series_mul(infinite_series):
    times_two = infinite_series * 2
    orig_values = list((acc.value for acc in islice(infinite_series, 10)))
    times_two_values = list((acc.value for acc in islice(times_two, 10)))
    assert times_two_values == [v * 2 for v in orig_values]

def test_accrual_series_rmul(infinite_series):
    times_two = 2 * infinite_series
    orig_values = list((acc.value for acc in islice(infinite_series, 10)))
    times_two_values = list((acc.value for acc in islice(times_two, 10)))
    assert times_two_values == [v * 2 for v in orig_values]
