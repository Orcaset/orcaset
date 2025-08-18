from datetime import date
import pytest
from orcaset.financial import Accrual, AccrualSeries, Period, YF


class TestAccrueNoOverlap:
    """Test accrue method when query period doesn't overlap with accrual series."""
    
    def test_query_before_all_accruals(self):
        """Query period entirely before all accruals."""
        accruals = [
            Accrual.act360(Period(date(2023, 2, 1), date(2023, 2, 15)), 100.0),
            Accrual.act360(Period(date(2023, 2, 15), date(2023, 3, 1)), 200.0),
        ]
        series = AccrualSeries(series=accruals)

        result = series.accrue(date(2023, 1, 1), date(2023, 2, 1))
        assert result == pytest.approx(0.0)
    
    def test_query_after_all_accruals(self):
        """Query period entirely after all accruals."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 15)), 100.0),
            Accrual.act360(Period(date(2023, 1, 15), date(2023, 2, 1)), 200.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 2, 2), date(2023, 3, 31))
        assert result == pytest.approx(0.0)
    
    def test_query_in_gap_between_accruals(self):
        """Query period in gap between non-consecutive accruals."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 15)), 100.0),
            Accrual.act360(Period(date(2023, 3, 1), date(2023, 3, 15)), 200.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 16), date(2023, 3, 1))
        assert result == pytest.approx(0.0)


class TestAccruePartialOverlap:
    """Test accrue method when query period partially overlaps with accruals."""
    
    def test_query_starts_before_ends_during_first_accrual(self):
        """Query starts before series, ends during first accrual."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 10), date(2023, 1, 20)), 100.0),
            Accrual.act360(Period(date(2023, 1, 20), date(2023, 1, 30)), 200.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 5), date(2023, 1, 15))
        
        expected = 100.0 * 5 / 10
        assert result == pytest.approx(expected)
    
    def test_query_starts_during_ends_after_last_accrual(self):
        """Query starts during accrual, ends after series."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 10)), 100.0),
            Accrual.act360(Period(date(2023, 1, 10), date(2023, 1, 20)), 200.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 15), date(2023, 1, 30))
        
        expected = 200.0 * 5 / 10
        assert result == pytest.approx(expected)
    
    def test_query_within_single_accrual(self):
        """Query period completely within a single accrual."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 31)), 310.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 10), date(2023, 1, 20))
        
        expected = 310.0 * 10 / 30
        assert result == pytest.approx(expected)


class TestAccrueCompleteOverlap:
    """Test accrue method when query period completely overlaps with accruals."""
    
    def test_query_exactly_matches_single_accrual(self):
        """Query period exactly matches a single accrual period."""
        accruals = [Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 31)), 310.0)]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 1), date(2023, 1, 31))
        assert result == pytest.approx(310.0)
    
    def test_query_encompasses_entire_series(self):
        """Query period encompasses entire accrual series."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 10), date(2023, 1, 20)), 100.0),
            Accrual.act360(Period(date(2023, 1, 20), date(2023, 1, 30)), 200.0),
            Accrual.act360(Period(date(2023, 1, 30), date(2023, 2, 10)), 300.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 5), date(2023, 2, 15))
        assert result == pytest.approx(600.0)
    
    def test_single_accrual_encompasses_query(self):
        """Single accrual period encompasses entire query period."""
        accruals = [Accrual.act360(Period(date(2023, 1, 1), date(2023, 3, 1)), 600.0)]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 15), date(2023, 2, 15))
        assert result == pytest.approx(600.0 * 31 / 59)


class TestAccrueMultiAccrualScenarios:
    """Test accrue method with complex multi-accrual scenarios."""
    
    def test_query_spans_accruals_with_gaps(self):
        """Query period spans accruals with gaps between them."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 10)), 100.0),
            Accrual.act360(Period(date(2023, 1, 20), date(2023, 1, 30)), 200.0),
            Accrual.act360(Period(date(2023, 2, 10), date(2023, 2, 20)), 300.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 1), date(2023, 2, 20))
        assert result == pytest.approx(600.0)
    
    def test_mixed_partial_complete_overlaps(self):
        """Query with mixed partial and complete overlaps across multiple accruals."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 11)), 100.0),   # 10 days
            Accrual.act360(Period(date(2023, 1, 11), date(2023, 1, 21)), 200.0),  # 10 days - complete
            Accrual.act360(Period(date(2023, 1, 21), date(2023, 2, 1)), 330.0),   # 11 days - partial
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 6), date(2023, 1, 26))
        assert result == pytest.approx((100.0 * 5/10) + 200.0 + (330.0 * 5/11))

    def test_query_touches_accrual_boundaries(self):
        """Query period boundaries align with accrual boundaries."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 15)), 150.0),
            Accrual.act360(Period(date(2023, 1, 15), date(2023, 2, 1)), 170.0),
            Accrual.act360(Period(date(2023, 2, 1), date(2023, 2, 15)), 150.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 15), date(2023, 2, 1))
        assert result == pytest.approx(170.0)


class TestAccrueEdgeCases:
    """Test accrue method edge cases."""
    
    def test_empty_accrual_series(self):
        """Test accrue with empty accrual series."""
        series = AccrualSeries(series=[])
        
        result = series.accrue(date(2023, 1, 1), date(2023, 1, 31))
        assert result == pytest.approx(0.0)
    
    def test_query_dates_equal(self):
        """Test accrue when query start and end dates are equal (zero period)."""
        accruals = [Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 31)), 310.0)]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 15), date(2023, 1, 15))
        assert result == pytest.approx(0.0)
    
    def test_negative_accrual_values(self):
        """Test accrue with negative accrual values."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 15)), -100.0),
            Accrual.act360(Period(date(2023, 1, 15), date(2023, 2, 1)), 200.0),
            Accrual.act360(Period(date(2023, 2, 1), date(2023, 2, 15)), -50.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 1), date(2023, 2, 15))
        assert result == pytest.approx(50.0)
    
    def test_different_year_fraction_methods(self):
        """Test accrue with accruals using different year fraction methods."""
        accruals = [
            Accrual(Period(date(2022, 12, 31), date(2023, 1, 31)), 150.0, YF.actual360),
            Accrual(Period(date(2023, 1, 31), date(2023, 2, 28)), 160.0, YF.thirty360),
            Accrual(Period(date(2023, 2, 28), date(2023, 3, 31)), 150.0, lambda _, __: 1),  # Constant
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 10), date(2023, 3, 10))
        
        first_partial = 150.0 * YF.actual360(date(2023, 1, 10), date(2023, 1, 31))/ YF.actual360(date(2022, 12, 31), date(2023, 1, 31))
        second_complete = 160.0
        third_partial = 150.0
        
        expected = first_partial + second_complete + third_partial
        assert result == pytest.approx(expected)
    
    def test_single_day_accruals(self):
        """Test accrue with single-day accrual periods."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 2)), 100.0),
            Accrual.act360(Period(date(2023, 1, 2), date(2023, 1, 3)), 200.0),
            Accrual.act360(Period(date(2023, 1, 3), date(2023, 1, 4)), 300.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 1), date(2023, 1, 4))
        assert result == pytest.approx(600.0)
    
    def test_query_exactly_at_accrual_boundary(self):
        """Test accrue when query boundaries exactly match accrual boundaries."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 15)), 150.0),
            Accrual.act360(Period(date(2023, 1, 15), date(2023, 2, 1)), 170.0),
            Accrual.act360(Period(date(2023, 2, 1), date(2023, 2, 15)), 150.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 15), date(2023, 2, 1))
        assert result == pytest.approx(170.0)


class TestAccrueComplexScenarios:
    """Test accrue method with complex real-world scenarios."""
    
    def test_irregular_accrual_periods(self):
        """Test with irregular, non-uniform accrual periods."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 5)), 40.0),     # 4 days
            Accrual.act360(Period(date(2023, 1, 5), date(2023, 1, 25)), 400.0),   # 20 days
            Accrual.act360(Period(date(2023, 1, 25), date(2023, 1, 27)), 6.0),    # 2 days
            Accrual.act360(Period(date(2023, 1, 27), date(2023, 2, 15)), 380.0),  # 19 days
        ]
        series = AccrualSeries(series=accruals)
        
        # Query overlaps all periods partially and completely
        result = series.accrue(date(2023, 1, 3), date(2023, 2, 10))
        
        # Expected: partial first + complete second + complete third + partial fourth
        first_partial = 40.0 * 2/4        # Jan 3-5: 2 out of 4 days
        second_complete = 400.0           # Complete
        third_complete = 6.0              # Complete
        fourth_partial = 380.0 * 14/19    # Jan 27-Feb 10: 14 out of 19 days
        
        expected = first_partial + second_complete + third_complete + fourth_partial
        assert result == pytest.approx(expected)
    
    def test_many_small_accruals(self):
        """Test with many small consecutive accruals."""
        accruals = []
        total_expected = 0.0
        
        # Create 30 daily accruals with incrementing values
        for i in range(30):
            start_date = date(2023, 1, 1 + i)
            end_date = date(2023, 1, 2 + i)
            value = float(i + 1) * 10  # 10, 20, 30, ..., 300
            accruals.append(Accrual.act360(Period(start_date, end_date), value))
            total_expected += value
        
        series = AccrualSeries(series=accruals)
        
        # Query encompasses all accruals
        result = series.accrue(date(2023, 1, 1), date(2023, 1, 31))
        assert result == pytest.approx(total_expected)
    
    def test_overlapping_query_boundaries_complex(self):
        """Test complex scenario with query boundaries creating multiple splits."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 20)), 200.0),   # 19 days
            Accrual.act360(Period(date(2023, 1, 20), date(2023, 2, 10)), 210.0),  # 21 days
            Accrual.act360(Period(date(2023, 2, 10), date(2023, 3, 1)), 190.0),   # 19 days
        ]
        series = AccrualSeries(series=accruals)
        
        # Query starts mid-first, ends mid-last
        result = series.accrue(date(2023, 1, 10), date(2023, 2, 20))
        
        # Expected: partial first + complete second + partial third
        first_partial = 200.0 * 10/19     # Jan 10-20: 10 out of 19 days
        second_complete = 210.0           # Complete
        third_partial = 190.0 * 10/19     # Feb 10-20: 10 out of 19 days
        
        expected = first_partial + second_complete + third_partial
        assert result == pytest.approx(expected)


class TestAccrueLazyEvaluation:
    """Test that accrue method respects lazy evaluation of accrual values."""
    
    def test_lazy_evaluation_only_evaluates_overlapping_accruals(self):
        """Test that only accruals overlapping with query period are evaluated."""
        from unittest.mock import Mock
        
        # Create mocks for values
        before_mock = Mock(return_value=100.0)
        overlap_mock = Mock(return_value=200.0)
        after_mock = Mock(return_value=300.0)
        
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 10)), before_mock),   # Before query
            Accrual.act360(Period(date(2023, 1, 15), date(2023, 1, 25)), overlap_mock), # Overlaps query
            Accrual.act360(Period(date(2023, 2, 1), date(2023, 2, 10)), after_mock),   # After query
        ]
        series = AccrualSeries(series=accruals)
        
        # Query only overlaps middle accrual
        result = series.accrue(date(2023, 1, 12), date(2023, 1, 30))
        
        # Only the overlapping accrual should be evaluated
        before_mock.assert_not_called()
        overlap_mock.assert_called_once()
        after_mock.assert_not_called()
        
        # Should get partial value from middle accrual
        expected = 200.0 * 10/10  # Jan 15-25: all 10 days within query period
        assert result == pytest.approx(expected)
    
    def test_lazy_evaluation_with_partial_overlaps(self):
        """Test lazy evaluation with accruals that need splitting."""
        from unittest.mock import Mock
        
        value_mock = Mock(return_value=300.0)
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 31)), value_mock),
        ]
        series = AccrualSeries(series=accruals)
        
        # Query partial overlap that requires splitting
        result = series.accrue(date(2023, 1, 10), date(2023, 1, 20))
        
        # Value should be evaluated when split occurs
        value_mock.assert_called_once()
        
        # Should get partial value (10 out of 30 days)
        expected = 300.0 * 10/30
        assert result == pytest.approx(expected)


class TestAccrueInvalidInputs:
    """Test accrue method with invalid inputs."""
    
    def test_dt1_after_dt2(self):
        """Test accrue when start date is after end date."""
        accruals = [
            Accrual.act360(Period(date(2023, 1, 1), date(2023, 1, 31)), 310.0),
        ]
        series = AccrualSeries(series=accruals)
        
        result = series.accrue(date(2023, 1, 20), date(2023, 1, 10))
        assert result == pytest.approx(310.0 * 10 / 30)