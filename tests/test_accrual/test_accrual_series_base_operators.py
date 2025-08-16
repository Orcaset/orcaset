from datetime import date
from unittest.mock import Mock

import pytest

from orcaset.financial.accrual import Accrual
from orcaset.financial.accrual_node import AccrualSeries
from orcaset.financial.period import Period
from orcaset.financial.yearfrac import YF


class TestAccrualSeriesBaseAddition:
    """Test __add__ and __radd__ operators for AccrualSeriesBase."""

    def test_add_accrual_series_same_dates(self):
        """Test adding two AccrualSeries with same dates."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        mock_value3 = Mock(return_value=50.0)
        mock_value4 = Mock(return_value=75.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 + series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        assert len(result) == 2
        assert result[0].period == Period(date(2023, 1, 1), date(2023, 1, 15))
        assert result[1].period == Period(date(2023, 1, 15), date(2023, 2, 1))
        assert result[0].value == 150.0
        assert result[1].value == 275.0

    def test_add_accrual_series_different_dates(self):
        """Test adding two AccrualSeries with different dates."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=300.0)
        mock_value3 = Mock(return_value=200.0)
        mock_value4 = Mock(return_value=400.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 20), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 10), date(2023, 1, 25)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 25), date(2023, 2, 10)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 + series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        # Verify resulting accruals
        assert [acc.period for acc in result] == [
            Period(date(2023, 1, 1), date(2023, 1, 10)),
            Period(date(2023, 1, 10), date(2023, 1, 15)),
            Period(date(2023, 1, 15), date(2023, 1, 20)),
            Period(date(2023, 1, 20), date(2023, 1, 25)),
            Period(date(2023, 1, 25), date(2023, 2, 1)),
            Period(date(2023, 2, 1), date(2023, 2, 10)),
        ]
        assert [acc.value for acc in result] == pytest.approx(
            [64.2857142857143, 102.380952380952, 66.6666666666667, 191.666666666667, 350.0, 225.0]
        )
        assert all([acc.yf == YF.actual360 for acc in result])

    def test_add_scalar_int(self):
        """Test adding an integer to AccrualSeries."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series + 50
        result = list(result_series)

        mock_value.assert_not_called()

        assert [acc.period for acc in result] == [Period(date(2023, 1, 1), date(2023, 1, 15))]
        assert result[0].value == 150.0

    def test_add_scalar_float(self):
        """Test adding a float to AccrualSeries."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series + 25.5
        result = list(result_series)

        mock_value.assert_not_called()

        assert [acc.period for acc in result] == [Period(date(2023, 1, 1), date(2023, 1, 15))]
        assert result[0].value == 125.5

    def test_radd_scalar(self):
        """Test reverse addition (scalar + AccrualSeries)."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = 50.0 + series
        result = list(result_series)

        mock_value.assert_not_called()

        assert [acc.period for acc in result] == [Period(date(2023, 1, 1), date(2023, 1, 15))]
        assert result[0].value == 150.0

    def test_add_empty_series(self):
        """Test adding with empty AccrualSeries."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series1 = AccrualSeries(series=accruals)
        series2 = AccrualSeries(series=[])

        result_series = series1 + series2
        result = list(result_series)

        mock_value.assert_not_called()

        assert accruals == result

    def test_add_invalid_type(self):
        """Test adding invalid type raises TypeError."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        with pytest.raises(TypeError):
            series + "invalid"  # type: ignore

        mock_value.assert_not_called()

    def test_add_different_yf(self):
        """Test adding accruals with different yield factors."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value2, YF.thirty360),
        ]
        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 + series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert [acc for acc in result] == [Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), 300.0, YF.na)]


class TestAccrualSeriesBaseSubtraction:
    """Test __sub__ operator for AccrualSeriesBase."""

    def test_sub_scalar_int(self):
        """Test subtracting an integer from AccrualSeries."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series - 25
        result = list(result_series)

        mock_value.assert_not_called()
        assert result == [Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), 75.0, YF.actual360)]

    def test_sub_scalar_float(self):
        """Test subtracting a float from AccrualSeries."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series - 12.5
        result = list(result_series)

        mock_value.assert_not_called()
        assert result == [Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), 87.5, YF.actual360)]

    def test_sub_multiple_accruals(self):
        """Test subtraction with multiple accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series - 50.0
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        
        assert result == [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), 50.0, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), 150.0, YF.actual360),
        ]
        assert result[1].value == 150.0  # 200 - 50
        assert result[0].value == 50.0  # 100 - 50

    def test_sub_accrual_series_same_dates(self):
        """Test subtracting two AccrualSeries with same dates."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        mock_value3 = Mock(return_value=50.0)
        mock_value4 = Mock(return_value=75.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 - series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        assert len(result) == 2
        assert result[0].period == Period(date(2023, 1, 1), date(2023, 1, 15))
        assert result[1].period == Period(date(2023, 1, 15), date(2023, 2, 1))
        assert result[0].value == 50.0
        assert result[1].value == 125.0

    def test_sub_accrual_series_different_dates(self):
        """Test subtracting two AccrualSeries with different dates."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=300.0)
        mock_value3 = Mock(return_value=200.0)
        mock_value4 = Mock(return_value=400.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 20), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 10), date(2023, 1, 25)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 25), date(2023, 2, 10)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 - series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        # Verify resulting accruals
        assert [acc.period for acc in result] == [
            Period(date(2023, 1, 1), date(2023, 1, 10)),
            Period(date(2023, 1, 10), date(2023, 1, 15)),
            Period(date(2023, 1, 15), date(2023, 1, 20)),
            Period(date(2023, 1, 20), date(2023, 1, 25)),
            Period(date(2023, 1, 25), date(2023, 2, 1)),
            Period(date(2023, 2, 1), date(2023, 2, 10)),
        ]
        # Check values in reversed order to test encapsulation
        result.reverse()
        assert [acc.value for acc in result] == pytest.approx(
            [-225, 0, 58.3333333333333, -66.6666666666667, -30.9523809523809, 64.2857142857143]
        )
        assert all([acc.yf == YF.actual360 for acc in result])

    def test_sub_empty_series(self):
        """Test subtraction with empty AccrualSeries."""
        series = AccrualSeries(series=[])

        result_series = series - 10.0
        result = list(result_series)

        # Should get empty result
        assert len(result) == 0

    def test_sub_invalid_type(self):
        """Test subtracting invalid type raises TypeError."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        with pytest.raises(TypeError):
            series - "invalid"  # type: ignore

        mock_value.assert_not_called()

    def test_sub_different_yf(self):
        """Test subtracting accruals with different yield factors."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value2, YF.thirty360),
        ]
        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 - series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert [acc for acc in result] == [Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), -100.0, YF.na)]


class TestAccrualSeriesBaseNegation:
    """Test __neg__ operator for AccrualSeriesBase."""

    def test_neg_single_accrual(self):
        """Test negation with single accrual."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = -series
        result = list(result_series)

        # Verify lazy evaluation
        mock_value.assert_not_called()

        # Verify result
        assert len(result) == 1
        assert result[0].value == -100.0

    def test_neg_multiple_accruals(self):
        """Test negation with multiple accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=-50.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = -series
        result = list(result_series)

        # Verify lazy evaluation
        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        # Verify results
        assert len(result) == 2
        assert result[0].value == -100.0  # -(100)
        assert result[1].value == 50.0  # -(-50)

    def test_neg_empty_series(self):
        """Test negation with empty AccrualSeries."""
        series = AccrualSeries(series=[])

        result_series = -series
        result = list(result_series)

        # Should get empty result
        assert len(result) == 0

    def test_double_negation(self):
        """Test double negation returns to original values."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = -(-series)
        result = list(result_series)

        # Verify lazy evaluation
        mock_value.assert_not_called()

        # Verify result
        assert len(result) == 1
        assert result[0].value == 100.0


class TestAccrualSeriesBaseMultiplication:
    """Test __mul__ and __rmul__ operators for AccrualSeriesBase."""

    def test_mul_accrual_series_same_date(self):
        """Test multiplying two AccrualSeries with same dates."""
        mock_value1 = Mock(return_value=2.0)
        mock_value2 = Mock(return_value=3.0)
        mock_value3 = Mock(return_value=4.0)
        mock_value4 = Mock(return_value=5.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 * series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        assert len(result) == 2
        assert result[1].period == Period(date(2023, 1, 15), date(2023, 2, 1))
        assert result[0].period == Period(date(2023, 1, 1), date(2023, 1, 15))
        assert result[1].value == 15.0
        assert result[0].value == 8.0

    def test_mul_accrual_series_different_dates(self):
        """Test multiplying two AccrualSeries with different dates."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=300.0)
        mock_value3 = Mock(return_value=200.0)
        mock_value4 = Mock(return_value=400.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 20), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 10), date(2023, 1, 25)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 25), date(2023, 2, 10)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 * series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        # Verify resulting accruals
        assert [acc.period for acc in result] == [
            Period(date(2023, 1, 1), date(2023, 1, 10)),
            Period(date(2023, 1, 10), date(2023, 1, 15)),
            Period(date(2023, 1, 15), date(2023, 1, 20)),
            Period(date(2023, 1, 20), date(2023, 1, 25)),
            Period(date(2023, 1, 25), date(2023, 2, 1)),
            Period(date(2023, 2, 1), date(2023, 2, 10)),
        ]
        assert [acc.value for acc in result] == pytest.approx(
            [0, 2380.95238095238, 0, 8333.33333333333, 30625, 0]
        )
        assert all([acc.yf == YF.actual360 for acc in result])

    def test_mul_scalar_int(self):
        """Test multiplying AccrualSeries by integer."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series * 3
        result = list(result_series)

        # Verify lazy evaluation
        mock_value.assert_not_called()

        # Verify result
        assert len(result) == 1
        assert result[0].value == 300.0  # 100 * 3

    def test_mul_scalar_float(self):
        """Test multiplying AccrualSeries by float."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series * 2.5
        result = list(result_series)

        # Verify lazy evaluation
        mock_value.assert_not_called()

        # Verify result
        assert len(result) == 1
        assert result[0].value == 250.0  # 100 * 2.5

    def test_rmul_scalar(self):
        """Test reverse multiplication (scalar * AccrualSeries)."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = 1.5 * series
        result = list(result_series)

        # Verify lazy evaluation
        mock_value.assert_not_called()

        # Verify result
        assert len(result) == 1
        assert result[0].value == 150.0  # 1.5 * 100

    def test_mul_multiple_accruals(self):
        """Test multiplication with multiple accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series * 0.5
        result = list(result_series)

        # Verify lazy evaluation
        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        # Verify results
        assert len(result) == 2
        assert result[0].value == 50.0  # 100 * 0.5
        assert result[1].value == 100.0  # 200 * 0.5

    def test_mul_zero(self):
        """Test multiplication by zero."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series * 0
        result = list(result_series)

        # Verify lazy evaluation
        mock_value.assert_not_called()

        # Verify result
        assert len(result) == 1
        assert result[0].value == 0.0

    def test_mul_invalid_type(self):
        """Test multiplication by invalid type raises TypeError."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        with pytest.raises(TypeError):
            series * "invalid"  # type: ignore

        # Verify lazy evaluation maintained
        mock_value.assert_not_called()

    def test_mul_empty_series(self):
        """Test multiplication with empty AccrualSeries."""
        series = AccrualSeries(series=[])

        result_series = series * 5.0
        result = list(result_series)

        # Should get empty result
        assert len(result) == 0

    def test_mul_different_yf(self):
        """Test multiplication with different year fractions."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.thirty360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series * 2.0
        result = list(result_series)

        # Verify lazy evaluation
        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        # Access value and verify
        assert result[0].value == 200.0  # 100 * 2
        assert result[1].value == 400.0  # 200 * 2

class TestAccrualSeriesBaseLazyEvaluation:
    """Test lazy evaluation behavior across all operators."""

    def test_chained_operations_lazy_evaluation(self):
        """Test that chained operations maintain lazy evaluation."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = ((series + 50) * 2) - 100
        result = list(result_series)

        # Verify lazy evaluation - mocks should not be called until value access
        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        # Now access values
        values = [accrual.value for accrual in result]

        # Verify calculations: ((100 + 50) * 2) - 100 = 200, ((200 + 50) * 2) - 100 = 400
        assert values[0] == 200.0
        assert values[1] == 400.0

    def test_complex_addition_lazy_evaluation(self):
        """Test lazy evaluation with complex addition scenarios."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        mock_value3 = Mock(return_value=50.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value2, YF.actual360),
        ]
        accruals3 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value3, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)
        series3 = AccrualSeries(series=accruals3)

        # Chain additions: series1 + series2 + series3
        result_series = series1 + series2 + series3
        result = list(result_series)

        # Verify lazy evaluation
        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()

        # Access value and verify
        assert result[0].value == 350.0  # 100 + 200 + 50

    def test_iterator_caching_with_operations(self):
        """Test that iterator caching works correctly with operations."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series + 50

        # First iteration
        result1 = list(result_series)
        # Second iteration
        result2 = list(result_series)

        # Verify lazy evaluation maintained
        mock_value.assert_not_called()

        # Verify both iterations give same objects (cached)
        assert len(result1) == len(result2) == 1
        assert result1[0] is result2[0]  # Same object due to caching

    def test_mixed_operations_different_dates_lazy_evaluation(self):
        """Test lazy evaluation with mixed operations on same date series."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)

        # Use same dates to avoid period splitting which triggers value access
        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value2, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        # Complex operation: (series1 + series2) * 2 - 50
        result_series = (series1 + series2) * 2 - 50
        result = list(result_series)

        # Verify lazy evaluation
        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        # Verify we get results
        assert len(result) == 1
        # Access values to ensure they work: (100 + 200) * 2 - 50 = 550
        assert result[0].value == 550.0


class TestAccrualSeriesBaseDivision:
    """Test __truediv__ operator for AccrualSeriesBase."""

    def test_truediv_accrual_series_same_dates(self):
        """Test dividing two AccrualSeries with same dates."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        mock_value3 = Mock(return_value=50.0)
        mock_value4 = Mock(return_value=25.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 / series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        assert len(result) == 2
        assert result[0].period == Period(date(2023, 1, 1), date(2023, 1, 15))
        assert result[1].period == Period(date(2023, 1, 15), date(2023, 2, 1))
        assert result[0].value == 2.0  # 100 / 50
        assert result[1].value == 8.0  # 200 / 25

    def test_truediv_accrual_series_different_dates(self):
        """Test dividing two AccrualSeries with different dates."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=300.0)
        mock_value3 = Mock(return_value=200.0)
        mock_value4 = Mock(return_value=400.0)

        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 20), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 10), date(2023, 1, 25)), mock_value3, YF.actual360),
            Accrual(Period(date(2023, 1, 25), date(2023, 2, 10)), mock_value4, YF.actual360),
        ]

        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 / series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        mock_value3.assert_not_called()
        mock_value4.assert_not_called()

        # Verify resulting accruals
        assert [acc.period for acc in result] == [
            Period(date(2023, 1, 1), date(2023, 1, 10)),
            Period(date(2023, 1, 10), date(2023, 1, 15)),
            Period(date(2023, 1, 15), date(2023, 1, 20)),
            Period(date(2023, 1, 20), date(2023, 1, 25)),
            Period(date(2023, 1, 25), date(2023, 2, 1)),
            Period(date(2023, 2, 1), date(2023, 2, 10)),
        ]

        for i, acc in enumerate(result):
            match i:
                case 0:
                    print(i)
                    with pytest.raises(ZeroDivisionError):
                        print('value for ', i, acc.value)
                case 1:
                    assert pytest.approx(acc.value) == 0.535714286
                case 2 | 5:
                    assert pytest.approx(acc.value) == 0
                case 3:
                    assert pytest.approx(acc.value) == 1.875
                case 4:
                    assert pytest.approx(acc.value) == 1
                case _:
                    raise AssertionError("Unexpected index in result.")

        assert all([acc.yf == YF.actual360 for acc in result])

    def test_truediv_scalar_int(self):
        """Test dividing AccrualSeries by integer."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series / 4
        result = list(result_series)

        mock_value.assert_not_called()

        assert [acc.period for acc in result] == [Period(date(2023, 1, 1), date(2023, 1, 15))]
        assert result[0].value == 25.0  # 100 / 4

    def test_truediv_scalar_float(self):
        """Test dividing AccrualSeries by float."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series / 2.5
        result = list(result_series)

        mock_value.assert_not_called()

        assert [acc.period for acc in result] == [Period(date(2023, 1, 1), date(2023, 1, 15))]
        assert result[0].value == 40.0  # 100 / 2.5

    def test_truediv_multiple_accruals(self):
        """Test division with multiple accruals."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=200.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), mock_value2, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series / 5.0
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()
        
        assert result == [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), 20.0, YF.actual360),
            Accrual(Period(date(2023, 1, 15), date(2023, 2, 1)), 40.0, YF.actual360),
        ]
        assert result[0].value == 20.0  # 100 / 5
        assert result[1].value == 40.0  # 200 / 5

    def test_truediv_by_zero_scalar(self):
        """Test division by zero scalar raises ZeroDivisionError."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        result_series = series / 0
        result = list(result_series)

        # Lazy evaluation - error only happens when value is accessed
        mock_value.assert_not_called()
        
        with pytest.raises(ZeroDivisionError):
            result[0].value

    def test_truediv_by_accrual_with_zero(self):
        """Test division by AccrualSeries containing zero values."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=0.0)
        
        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value2, YF.actual360),
        ]
        
        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 / series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        with pytest.raises(ZeroDivisionError):
            result[0].value

    def test_truediv_empty_series(self):
        """Test division with empty AccrualSeries."""
        series = AccrualSeries(series=[])

        result_series = series / 10.0
        result = list(result_series)

        assert len(result) == 0

    def test_truediv_invalid_type(self):
        """Test division by invalid type raises TypeError."""
        mock_value = Mock(return_value=100.0)
        accruals = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value, YF.actual360),
        ]
        series = AccrualSeries(series=accruals)

        with pytest.raises(TypeError):
            series / "invalid"  # type: ignore

        mock_value.assert_not_called()

    def test_truediv_different_yf(self):
        """Test dividing accruals with different yield factors."""
        mock_value1 = Mock(return_value=100.0)
        mock_value2 = Mock(return_value=50.0)
        accruals1 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value1, YF.actual360),
        ]
        accruals2 = [
            Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), mock_value2, YF.thirty360),
        ]
        series1 = AccrualSeries(series=accruals1)
        series2 = AccrualSeries(series=accruals2)

        result_series = series1 / series2
        result = list(result_series)

        mock_value1.assert_not_called()
        mock_value2.assert_not_called()

        assert [acc for acc in result] == [Accrual(Period(date(2023, 1, 1), date(2023, 1, 15)), 2.0, YF.na)]


class TestAccrualSeriesBaseEdgeCases:
    """Test edge cases and error conditions."""

    def test_operations_with_empty_series(self):
        """Test all operations work correctly with empty series."""
        empty_series = AccrualSeries(series=[])

        # Test all operations
        assert list(empty_series + 10) == []
        assert list(empty_series - 10) == []
        assert list(empty_series * 10) == []
        assert list(empty_series / 10) == []
        assert list(-empty_series) == []

        # Test with another empty series
        empty_series2 = AccrualSeries(series=[])
        assert list(empty_series + empty_series2) == []

    def test_operations_preserve_period_and_yf(self):
        """Test that operations preserve period and year fraction information."""
        period = Period(date(2023, 1, 1), date(2023, 1, 15))
        mock_value = Mock(return_value=100.0)
        accrual = Accrual(period, mock_value, YF.cmonthly)
        series = AccrualSeries(series=[accrual])

        # Test various operations preserve metadata
        operations = [
            series + 50,
            series - 25,
            series * 2,
            series / 4,
            -series,
        ]

        for op_result in operations:
            result = list(op_result)
            assert len(result) == 1
            assert result[0].period == period
            assert result[0].yf == YF.cmonthly
            mock_value.assert_not_called()

