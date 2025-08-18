from datetime import date
from unittest.mock import Mock

import pytest

from orcaset.financial import YF, Accrual, AccrualSeries, Period


class TestAccrualSeriesBaseRebase:
    def test_rebase_no_overlap_periods(self):
        """Test rebase() with periods that don't overlap with existing accruals - should return zero accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 28), date(2023, 3, 31)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 31), date(2023, 4, 30)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        new_periods = [
            Period(date(2023, 1, 1), date(2023, 1, 15)),
            Period(date(2023, 5, 1), date(2023, 6, 1)),
        ]

        result = series.rebase(new_periods)
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert result_list == [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), 0.0, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 28)), 0.0, YF.actual360),
            Accrual(Period(date(2023, 2, 28), date(2023, 3, 31)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 31), date(2023, 4, 30)), mock_value2, YF.actual360),
            Accrual(Period(date(2023, 4, 30), date(2023, 5, 1)), 0.0, YF.actual360),
            Accrual(Period(date(2023, 5, 1), date(2023, 6, 1)), 0.0, YF.actual360),
        ]

    def test_rebase_exact_match_periods(self):
        """Test rebase() with periods that exactly match existing accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        new_periods = [
            Period(date(2023, 2, 1), date(2023, 3, 1)),
            Period(date(2023, 3, 1), date(2023, 4, 1)),
        ]

        result = series.rebase(new_periods)
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert result_list == accruals

    def test_rebase_split_periods(self):
        """Test rebase() with periods that require splitting existing accruals."""
        mock_value = Mock(return_value=100.0)

        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 3, 1)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        new_periods = [
            Period(date(2023, 1, 15), date(2023, 2, 15)),
        ]

        result = series.rebase(new_periods)
        result_list = list(result)

        mock_value.assert_not_called()

        first_acc, second_pt = accruals[0].split(date(2023, 1, 15))
        second_acc, third_acc = second_pt.split(date(2023, 2, 15))

        expected_accruals = [first_acc, second_acc, third_acc]

        assert result_list == expected_accruals

    def test_rebase_overlapping_new_periods(self):
        """Test rebase() with new periods that span multiple original accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        new_periods = [
            Period(date(2023, 2, 15), date(2023, 3, 15)),
        ]

        result = series.rebase(new_periods)
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        expected_accruals = [*accruals[0].split(date(2023, 2, 15)), *accruals[1].split(date(2023, 3, 15))]

        assert result_list == expected_accruals

    def test_rebase_empty_series(self):
        """Test rebase() with an empty accrual series."""
        series = AccrualSeries(series=[])

        new_periods = [
            Period(date(2023, 1, 1), date(2023, 2, 1)),
            Period(date(2023, 2, 1), date(2023, 3, 1)),
        ]

        result = series.rebase(new_periods)
        result_list = list(result)

        assert len(result_list) == 2
        assert result_list[0].period == Period(date(2023, 1, 1), date(2023, 2, 1))
        assert result_list[0].value == 0.0
        assert result_list[1].period == Period(date(2023, 2, 1), date(2023, 3, 1))
        assert result_list[1].value == 0.0

    def test_rebase_empty_periods(self):
        """Test rebase() with empty new periods - should return original series."""
        mock_value = Mock(return_value=100.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result = series.rebase([])
        result_list = list(result)

        mock_value.assert_not_called()

        assert result_list == accruals

    def test_rebase_complex_scenario(self):
        """Test rebase() with a complex scenario involving multiple splits and overlaps."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        mock_value3 = Mock(return_value=300.0)

        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 2, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
            Accrual(Period(date(2023, 5, 1), date(2023, 6, 1)), mock_value3, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        new_periods = [
            Period(date(2022, 12, 15), date(2023, 1, 15)),  # Overlaps with first
            Period(date(2023, 2, 15), date(2023, 3, 15)),  # Gap then overlaps with second
            Period(date(2023, 4, 15), date(2023, 5, 15)),  # Gap then overlaps with third
        ]

        result = series.rebase(new_periods)
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()

        expected_accruals = [
            Accrual.act360(Period(date(2022, 12, 15), date(2023, 1, 1)), 0.0),
            *accruals[0].split(date(2023, 1, 15)),
            Accrual.act360(Period(date(2023, 2, 1), date(2023, 2, 15)), 0.0),
            Accrual.act360(Period(date(2023, 2, 15), date(2023, 3, 1)), 0.0),
            *accruals[1].split(date(2023, 3, 15)),
            Accrual.act360(Period(date(2023, 4, 1), date(2023, 4, 15)), 0.0),
            Accrual.act360(Period(date(2023, 4, 15), date(2023, 5, 1)), 0.0),
            *accruals[2].split(date(2023, 5, 15)),
        ]

        assert expected_accruals == result_list

