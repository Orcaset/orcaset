from datetime import date
from unittest.mock import Mock

import pytest

from orcaset.financial import YF, Accrual, AccrualSeries, Period


class TestAccrualSeriesBaseAfter:
    def test_after_date_before_all_accruals(self):
        """Test after() with a date before all accruals - should return all accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result = series.after(date(2023, 1, 15))
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert result_list == accruals

    def test_after_date_on_start_date(self):
        """Test after() with a date exactly on the start date of first accrual."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result = series.after(date(2023, 2, 1))
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert result_list == accruals

    def test_after_date_on_end_date(self):
        """Test after() with a date exactly on the end date of last accrual."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result = series.after(date(2023, 4, 1))
        result_list = list(result)

        assert len(result_list) == 0

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

    def test_after_date_during_first_period(self):
        """Test after() with a date during the first accrual period."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        split_date = date(2023, 2, 15)
        result = series.after(split_date)
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert result_list == [
            Accrual(Period(date(2023, 2, 15), date(2023, 3, 1)), 50.0, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]

    def test_after_date_during_middle_period(self):
        """Test after() with a date during a middle accrual period."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        mock_value3 = Mock(return_value=300.0)

        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 2, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value2, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value3, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        split_date = date(2023, 2, 15)
        result = series.after(split_date)
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()

        assert result_list == [
            Accrual(Period(date(2023, 2, 15), date(2023, 3, 1)), 100.0, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), 300.0, YF.actual360),
        ]

    def test_after_date_during_last_period(self):
        """Test after() with a date during the last accrual period."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        split_date = date(2023, 3, 15)
        result = series.after(split_date)
        result_list = list(result)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert len(result_list) == 1
        assert result_list[0].value == pytest.approx(109.6774194)
        assert result_list[0].period == Period(split_date, date(2023, 4, 1))

    def test_after_date_after_all_accruals(self):
        """Test after() with a date after all accruals - should return empty series."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        accruals = [
            Accrual(Period(date(2023, 2, 1), date(2023, 3, 1)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 3, 1), date(2023, 4, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result = series.after(date(2023, 5, 1))
        result_list = list(result)

        assert len(result_list) == 0

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

    def test_after_empty_series(self):
        """Test after() with an empty accrual series."""
        series = AccrualSeries(series=[])

        result = series.after(date(2023, 1, 1))
        result_list = list(result)

        assert len(result_list) == 0
