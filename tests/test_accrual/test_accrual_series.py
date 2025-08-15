from dataclasses import dataclass
from datetime import date
from typing import Iterable

from orcaset.financial import YF, Accrual, AccrualSeriesBase, Period


def test_accrual_series_addition():
    accruals = [
        Accrual(Period(date(2023, 1, 1), date(2023, 2, 1)), 1000, YF.cmonthly),
        Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), 2000, YF.cmonthly),
    ]

    @dataclass
    class AccrualSeriesSubclass[P](AccrualSeriesBase[P]):
        def _accruals(self) -> Iterable[Accrual]:
            return accruals

    series1 = AccrualSeriesSubclass()
    series2 = AccrualSeriesSubclass()
    series3 = AccrualSeriesSubclass()

    doubled_accruals = [
        Accrual(Period(date(2023, 1, 1), date(2023, 2, 1)), 2000, YF.cmonthly),
        Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), 4000, YF.cmonthly),
    ]

    tripled_accruals = [
        Accrual(Period(date(2023, 1, 1), date(2023, 2, 1)), 3000, YF.cmonthly),
        Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), 6000, YF.cmonthly),
    ]

    assert list(iter(series1 + series2)) == doubled_accruals
    assert list(iter(series1 + series2 + series3)) == tripled_accruals

