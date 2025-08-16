from datetime import date
from orcaset.financial import Accrual, AccrualSeries, Period, YF
import pytest


def test_w_avg_single_accrual():
    """Test w_avg with a single accrual covering the entire period."""
    accrual = Accrual.act360(Period(date(2023, 1, 1), date(2023, 2, 1)), 100.0)
    series = AccrualSeries(series=[accrual])
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 2, 1))
    assert result == pytest.approx(100.0)


def test_w_avg_multiple_accruals_same_value():
    """Test w_avg with multiple accruals having the same value."""
    accruals = [
        Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 15)), 50.0),
        Accrual.act360(Period(date(2023, 1, 15), date(2023, 2, 1)), 50.0),
    ]
    series = AccrualSeries(series=accruals)
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 2, 1))
    assert result == pytest.approx(50.0)


def test_w_avg_multiple_accruals_different_values():
    """Test w_avg with multiple accruals having different values."""
    accruals = [
        Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 16)), 100.0),  # 15 days
        Accrual.act360(Period(date(2023, 1, 16), date(2023, 2, 1)), 200.0),  # 16 days
    ]
    series = AccrualSeries(series=accruals)
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 2, 1))
    
    # Calculate expected weighted average
    # Weight1 = 15/360, Weight2 = 16/360
    # Weighted avg = (100 * 15/360 + 200 * 16/360) / (15/360 + 16/360)
    # = (100 * 15 + 200 * 16) / (15 + 16) = (1500 + 3200) / 31 = 4700 / 31 ≈ 151.61
    expected = (100.0 * 15 + 200.0 * 16) / (15 + 16)
    assert result == pytest.approx(expected)


def test_w_avg_partial_period():
    """Test w_avg with a query period that only partially overlaps accruals."""
    accruals = [
        Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 31)), 100.0),
        Accrual.act360(Period(date(2023, 1, 31), date(2023, 2, 28)), 200.0),
    ]
    series = AccrualSeries(series=accruals)
    
    # Query for middle portion: Jan 15 to Feb 15
    result = series.w_avg(date(2023, 1, 15), date(2023, 2, 15))
    
    # Should include:
    # - Jan 15-31: 16 days at 100.0
    # - Jan 31-Feb 15: 15 days at 200.0
    expected = (100.0 * 16 + 200.0 * 15) / (16 + 15)
    assert result == pytest.approx(expected)


def test_w_avg_no_overlap():
    """Test w_avg with a query period that doesn't overlap any accruals."""
    accruals = [
        Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 31)), 100.0),
    ]
    series = AccrualSeries(series=accruals)
    
    # Query for period after all accruals
    result = series.w_avg(date(2023, 3, 1), date(2023, 3, 31))
    assert result == pytest.approx(0.0)


def test_w_avg_empty_series():
    """Test w_avg with an empty accrual series."""
    series = AccrualSeries(series=[])
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 2, 1))
    assert result == pytest.approx(0.0)


def test_w_avg_zero_weight():
    """Test w_avg when total weight is zero (edge case)."""
    # Create an accrual with same start and end date (zero period)
    accrual = Accrual(Period(date(2023, 1, 1), date(2023, 1, 1)), 100.0, YF.actual360)
    series = AccrualSeries(series=[accrual])
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 1, 1))
    assert result == pytest.approx(0.0)


def test_w_avg_single_day_periods():
    """Test w_avg with single-day periods."""
    accruals = [
        Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 2)), 100.0),
        Accrual.act360(Period(date(2023, 1, 2), date(2023, 1, 3)), 200.0),
        Accrual.act360(Period(date(2023, 1, 3), date(2023, 1, 4)), 300.0),
    ]
    series = AccrualSeries(series=accruals)
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 1, 4))
    
    # Each period has equal weight (1 day), so simple average
    expected = (100.0 + 200.0 + 300.0) / 3
    assert result == pytest.approx(expected)


def test_w_avg_different_year_fraction_methods():
    """Test w_avg with accruals using different year fraction methods."""
    accruals = [
        Accrual(Period(date(2023, 1, 1), date(2023, 1, 16)), 100.0, YF.actual360),
        Accrual(Period(date(2023, 1, 16), date(2023, 2, 1)), 200.0, YF.thirty360),
    ]
    series = AccrualSeries(series=accruals)
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 2, 1))
    
    # Calculate expected with different year fractions
    weight1 = YF.actual360(date(2023, 1, 1), date(2023, 1, 16))
    weight2 = YF.thirty360(date(2023, 1, 16), date(2023, 2, 1))
    expected = (100.0 * weight1 + 200.0 * weight2) / (weight1 + weight2)
    assert result == pytest.approx(expected)


def test_w_avg_negative_values():
    """Test w_avg with negative accrual values."""
    accruals = [
        Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 16)), -100.0),
        Accrual.act360(Period(date(2023, 1, 16), date(2023, 2, 1)), 200.0),
    ]
    series = AccrualSeries(series=accruals)
    
    result = series.w_avg(date(2023, 1, 1), date(2023, 2, 1))
    
    # Should handle negative values correctly
    expected = (-100.0 * 15 + 200.0 * 16) / (15 + 16)
    assert result == pytest.approx(expected)


def test_w_avg_spanning_multiple_periods():
    """Test w_avg with a query period that spans multiple accrual periods."""
    accruals = [
        Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 11)), 100.0),   # 10 days
        Accrual.act360(Period(date(2023, 1, 11), date(2023, 1, 21)), 200.0),  # 10 days
        Accrual.act360(Period(date(2023, 1, 21), date(2023, 2, 1)), 300.0),   # 11 days
        Accrual.act360(Period(date(2023, 2, 1), date(2023, 2, 11)), 400.0),   # 10 days
        Accrual.act360(Period(date(2023, 2, 11), date(2023, 2, 21)), 500.0),  # 10 days
    ]
    series = AccrualSeries(series=accruals)
    
    # Query period spans from middle of second accrual to middle of fourth accrual
    result = series.w_avg(date(2023, 1, 16), date(2023, 2, 6))
    
    # Should include:
    # - Jan 16-21: 5 days at 200.0 (partial second accrual)
    # - Jan 21-Feb 1: 11 days at 300.0 (full third accrual)  
    # - Feb 1-6: 5 days at 400.0 (partial fourth accrual)
    expected = (200.0 * 5 + 300.0 * 11 + 400.0 * 5) / (5 + 11 + 5)
    assert result == pytest.approx(expected)

