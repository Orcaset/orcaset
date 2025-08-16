from datetime import date
from unittest.mock import Mock

import pytest

from orcaset.financial import Accrual, Period
from orcaset.financial.yearfrac import YF


class TestAccrualInit:
    def test_init_with_float_value(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual(period, 100.0, YF.actual360)
        
        assert accrual.period == period
        assert accrual.value == 100.0
        assert accrual.yf == YF.actual360

    def test_init_with_callable_value(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual(period, lambda: 150.0, YF.cmonthly)
        
        assert accrual.period == period
        assert accrual.value == 150.0
        assert accrual.yf == YF.cmonthly


class TestAccrualClassMethods:
    def test_act360(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        assert accrual.period == period
        assert accrual.value == 100.0
        assert accrual.yf == YF.actual360

    def test_cmonthly(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.cmonthly(period, 200.0)
        
        assert accrual.period == period
        assert accrual.value == 200.0
        assert accrual.yf == YF.cmonthly

    def test_thirty360(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.thirty360(period, 300.0)
        
        assert accrual.period == period
        assert accrual.value == 300.0
        assert accrual.yf == YF.thirty360


class TestAccrualValue:
    def test_value_caching_with_callable(self):
        value = Mock(return_value=42.0)
        
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual(period, value, YF.actual360)

        # First access should call the function
        value.assert_not_called()
        assert accrual.value == 42.0
        value.assert_called_once()
        
        # Second access should use cached value
        assert accrual._value == 42.0
        assert accrual.value == 42.0
        value.assert_called_once()

    def test_value_with_static_float(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual(period, 75.5, YF.actual360)
        
        assert accrual.value == 75.5


class TestAccrualSplit:
    def test_split_valid_date(self):
        value = Mock(return_value=360.0)
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, value)
        split_date = date(2023, 6, 1)
        
        first, second = accrual.split(split_date)
        value.assert_not_called()

        assert first.period.start == period.start
        assert first.period.end == split_date
        assert second.period.start == split_date
        assert second.period.end == period.end
        
        # Values should sum to original
        assert abs((first.value + second.value) - 360.0) < 1e-10

    def test_split_invalid_date_before_start(self):
        value = Mock(return_value=100.0)
        period = Period(date(2023, 6, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, value)

        with pytest.raises(ValueError, match="Split date .* must be within the accrual period"):
            accrual.split(date(2023, 1, 1))
        value.assert_not_called()

    def test_split_invalid_date_after_end(self):
        value = Mock(return_value=100.0)
        period = Period(date(2023, 1, 1), date(2023, 6, 30))
        accrual = Accrual.act360(period, value)
        
        with pytest.raises(ValueError, match="Split date .* must be within the accrual period"):
            accrual.split(date(2023, 12, 31))
        value.assert_not_called()

    def test_split_edge_cases(self):
        value = Mock(return_value=100.0)
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, value)
        
        # Test at start date (should fail)
        with pytest.raises(ValueError):
            accrual.split(period.start)
        
        # Test at end date (should fail)
        with pytest.raises(ValueError):
            accrual.split(period.end)
        
        value.assert_not_called()


class TestAccrualArithmetic:
    def test_add_float(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = accrual + 50.0
        
        assert result.value == 150.0
        assert result.period == period
        assert result.yf == accrual.yf

    def test_add_int(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = accrual + 25
        
        assert result.value == 125.0

    def test_radd(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = 50.0 + accrual
        
        assert result.value == 150.0

    def test_add_invalid_type(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        with pytest.raises(TypeError, match="Unsupported operand type"):
            accrual + "invalid"  # type: ignore

    def test_sub_float(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = accrual - 25.0
        
        assert result.value == 75.0

    def test_sub_invalid_type(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        with pytest.raises(TypeError, match="Unsupported operand type"):
            accrual - "invalid"  # type: ignore

    def test_mul_float(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = accrual * 2.5
        
        assert result.value == 250.0

    def test_rmul(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = 2.0 * accrual
        
        assert result.value == 200.0

    def test_mul_invalid_type(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        with pytest.raises(TypeError, match="Unsupported operand type"):
            accrual * "invalid"  # type: ignore

    def test_truediv_float(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = accrual / 4.0
        
        assert result.value == 25.0

    def test_truediv_invalid_type(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        with pytest.raises(TypeError, match="Unsupported operand type"):
            accrual / "invalid"  # type: ignore

    def test_neg(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        result = -accrual
        
        assert result.value == -100.0
        assert result.period == period
        assert result.yf == accrual.yf


class TestAccrualEquality:
    def test_equal_accruals(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual1 = Accrual.act360(period, 100.0)
        accrual2 = Accrual.act360(period, 100.0)
        
        assert accrual1 == accrual2

    def test_different_periods(self):
        period1 = Period(date(2023, 1, 1), date(2023, 12, 31))
        period2 = Period(date(2024, 1, 1), date(2024, 12, 31))
        accrual1 = Accrual.act360(period1, 100.0)
        accrual2 = Accrual.act360(period2, 100.0)
        
        assert accrual1 != accrual2

    def test_different_values(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual1 = Accrual.act360(period, 100.0)
        accrual2 = Accrual.act360(period, 200.0)
        
        assert accrual1 != accrual2

    def test_different_yf(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual1 = Accrual.act360(period, 100.0)
        accrual2 = Accrual.cmonthly(period, 100.0)
        
        assert accrual1 != accrual2

    def test_not_equal_to_non_accrual(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        assert accrual != "not an accrual"
        assert accrual != 100.0
        assert accrual != None


class TestAccrualRepr:
    def test_repr_with_float_value(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        repr_str = repr(accrual)
        assert repr_str == "Accrual(period=Period(2023-01-01, 2023-12-31), value=100.0, yf=YF.actual360)"

    def test_repr_with_callable_value(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual(period, lambda: 100.0, YF.actual360)
        
        repr_str = repr(accrual)
        assert repr_str == "Accrual(period=Period(2023-01-01, 2023-12-31), value=() -> float, yf=YF.actual360)"


class TestAccrualChainedOperations:
    def test_chained_arithmetic_operations(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual.act360(period, 100.0)
        
        # Test: -((((100 + 50) * 2) / 10) - 25) = -5
        result = -((((accrual + 50) * 2) / 10) - 25)
        assert result.value == -5.0
        assert result.period == period
        assert result.yf == YF.actual360

    def test_lazy_evaluation_in_operations(self):
        value = Mock(return_value=100.0)
        
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        accrual = Accrual(period, value, YF.actual360)

        # Create a chain of operations but don't access value yet
        result = -((((accrual + 50) * 2) / 10) - 25)
        value.assert_not_called()

        # Now access the value
        assert result.value == -5.0
        value.assert_called_once()


class TestAccrualLazyEvaluation:
    def test_add_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func = Mock(return_value=100.0)
        accrual = Accrual(period, mock_func, YF.actual360)
        
        result = accrual + 50.0
        mock_func.assert_not_called()
        
        assert result.value == 150.0
        mock_func.assert_called_once()

    def test_radd_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func = Mock(return_value=100.0)
        accrual = Accrual(period, mock_func, YF.actual360)
        
        result = 50.0 + accrual
        mock_func.assert_not_called()
        
        assert result.value == 150.0
        mock_func.assert_called_once()

    def test_sub_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func = Mock(return_value=100.0)
        accrual = Accrual(period, mock_func, YF.actual360)
        
        result = accrual - 30.0
        mock_func.assert_not_called()
        
        assert result.value == 70.0
        mock_func.assert_called_once()

    def test_mul_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func = Mock(return_value=100.0)
        accrual = Accrual(period, mock_func, YF.actual360)
        
        result = accrual * 2.0
        mock_func.assert_not_called()
        
        assert result.value == 200.0
        mock_func.assert_called_once()

    def test_rmul_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func = Mock(return_value=100.0)
        accrual = Accrual(period, mock_func, YF.actual360)
        
        result = 2.0 * accrual
        mock_func.assert_not_called()
        
        assert result.value == 200.0
        mock_func.assert_called_once()

    def test_truediv_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func = Mock(return_value=100.0)
        accrual = Accrual(period, mock_func, YF.actual360)
        
        result = accrual / 2.0
        mock_func.assert_not_called()
        
        assert result.value == 50.0
        mock_func.assert_called_once()

    def test_neg_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func = Mock(return_value=100.0)
        accrual = Accrual(period, mock_func, YF.actual360)
        
        result = -accrual
        mock_func.assert_not_called()
        
        assert result.value == -100.0
        mock_func.assert_called_once()

    def test_eq_lazy_evaluation(self):
        period = Period(date(2023, 1, 1), date(2023, 12, 31))
        mock_func1 = Mock(return_value=100.0)
        mock_func2 = Mock(return_value=100.0)
        accrual1 = Accrual(period, mock_func1, YF.actual360)
        accrual2 = Accrual(period, mock_func2, YF.actual360)
        
        result = accrual1 == accrual2
        assert result is True
        mock_func1.assert_called_once()
        mock_func2.assert_called_once()
