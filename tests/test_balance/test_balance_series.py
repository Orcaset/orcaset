import datetime
from unittest.mock import Mock

import pytest

from orcaset.financial.balance_node import Balance, BalanceSeries
from orcaset.financial.yearfrac import YF


def test_balance_series_creation():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    result = list(series)
    assert result == balances
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()


def test_balance_series_iter_cache():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = BalanceSeries(series=balances)

    result1 = [s for s in series]
    result2 = [s for s in series]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    for r1, r2 in zip(result1, result2):
        assert r1 is r2


def test_balance_series_at_exact_date():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    assert series.at(datetime.date(2023, 1, 1)) == 100.0
    assert series.at(datetime.date(2023, 1, 3)) == 300.0


def test_balance_series_at_intermediate_date():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    assert series.at(datetime.date(2023, 1, 2)) == 100.0
    mock_value2.assert_not_called()


def test_balance_series_at_before_range():
    mock_value1 = Mock(return_value=200.0)
    mock_value2 = Mock(return_value=300.0)
    balances = [
        Balance(datetime.date(2023, 1, 2), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    assert series.at(datetime.date(2023, 1, 1)) == 0.0
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()


def test_balance_series_at_after_range():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    assert series.at(datetime.date(2023, 1, 5)) == 200.0


def test_balance_series_rebase_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    new_dates = [
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 3),
    ]
    rebased = series.rebase(new_dates)
    result = list(rebased)

    assert [b.date for b in result] == new_dates
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    assert [b.value for b in rebased] == [100.0, 200.0]


def test_balance_series_rebase():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    new_dates = [
        datetime.date(2022, 1, 1),
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 4),
    ]
    rebased = series.rebase(new_dates)
    result = list(rebased)

    expected_dates = [
        datetime.date(2022, 1, 1),
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 3),
        datetime.date(2023, 1, 4),
    ]
    assert [b.date for b in result] == expected_dates
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    assert [b.value for b in result] == [0.0, 100.0, 100.0, 300.0, 300.0]


def test_balance_series_after():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=300.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
        Balance(datetime.date(2023, 1, 3), mock_value3),
    ]
    series = BalanceSeries(series=balances)
    after_series = series.after(datetime.date(2023, 1, 1))
    result = list(after_series)

    expected = [
        Balance(datetime.date(2023, 1, 2), mock_value2),
        Balance(datetime.date(2023, 1, 3), mock_value3),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    assert result == expected


def test_balance_series_add_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=50.0)
    mock_value4 = Mock(return_value=75.0)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 1), mock_value3),
        Balance(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 + series2
    result = list(result_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), 150.0),
        Balance(datetime.date(2023, 1, 2), 275.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert result == expected


def test_balance_series_add_different_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    mock_value3 = Mock(return_value=200.0)
    mock_value4 = Mock(return_value=400.0)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 2), mock_value3),
        Balance(datetime.date(2023, 1, 4), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 + series2
    result = list(result_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), 100.0),
        Balance(datetime.date(2023, 1, 2), 300.0),
        Balance(datetime.date(2023, 1, 3), 500.0),
        Balance(datetime.date(2023, 1, 4), 700.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert [b.date for b in result] == [b.date for b in expected]
    assert [b.value for b in result] == [b.value for b in expected]

def test_balance_series_add_scalar():
    mock_value = Mock(return_value=100.0)
    series = BalanceSeries(series=[Balance(datetime.date(2023, 1, 1), mock_value)])
    result = series + 50.0
    expected = [
        Balance(datetime.date(2023, 1, 1), 150.0),
    ]
    mock_value.assert_not_called()
    assert list(result) == expected


def test_balance_series_add_invalid_type():
    mock_value = Mock(return_value=100.0)
    balances = [Balance(datetime.date(2023, 1, 1), mock_value)]
    series = BalanceSeries(series=balances)

    with pytest.raises(TypeError, match="Cannot add"):
        series + "invalid"  # type: ignore
    mock_value.assert_not_called()


def test_balance_series_neg():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=-200.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    neg_series = -series
    result = list(neg_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), -100.0),
        Balance(datetime.date(2023, 1, 2), 200.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    assert result == expected


def test_balance_series_empty():
    series = BalanceSeries(series=[])
    assert list(series) == []
    assert series.at(datetime.date(2023, 1, 1)) == 0.0


def test_balance_series_sub_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=50.0)
    mock_value4 = Mock(return_value=75.0)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 1), mock_value3),
        Balance(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 - series2
    result = list(result_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), 50.0),
        Balance(datetime.date(2023, 1, 2), 125.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert result == expected


def test_balance_series_sub_different_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    mock_value3 = Mock(return_value=200.0)
    mock_value4 = Mock(return_value=400.0)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 2), mock_value3),
        Balance(datetime.date(2023, 1, 4), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 - series2
    result = list(result_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), 100.0),
        Balance(datetime.date(2023, 1, 2), -100.0),
        Balance(datetime.date(2023, 1, 3), 100.0),
        Balance(datetime.date(2023, 1, 4), -100.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert [b.date for b in result] == [b.date for b in expected]
    assert [b.value for b in result] == [b.value for b in expected]


def test_balance_series_sub_scalar():
    mock_value = Mock(return_value=100.0)
    series = BalanceSeries(series=[Balance(datetime.date(2023, 1, 1), mock_value)])
    result = series - 25.0
    expected = [
        Balance(datetime.date(2023, 1, 1), 75.0),
    ]
    mock_value.assert_not_called()
    assert list(result) == expected


def test_balance_series_sub_invalid_type():
    mock_value = Mock(return_value=100.0)
    balances = [Balance(datetime.date(2023, 1, 1), mock_value)]
    series = BalanceSeries(series=balances)

    with pytest.raises(TypeError, match="Cannot subtract"):
        series - "invalid"  # type: ignore
    mock_value.assert_not_called()


def test_balance_series_mul_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=2.0)
    mock_value4 = Mock(return_value=1.5)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 1), mock_value3),
        Balance(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 * series2
    result = list(result_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), 200.0),
        Balance(datetime.date(2023, 1, 2), 300.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert result == expected


def test_balance_series_mul_different_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    mock_value3 = Mock(return_value=2.0)
    mock_value4 = Mock(return_value=0.5)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 2), mock_value3),
        Balance(datetime.date(2023, 1, 4), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 * series2
    result = list(result_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), 0.0),
        Balance(datetime.date(2023, 1, 2), 200.0),
        Balance(datetime.date(2023, 1, 3), 600.0),
        Balance(datetime.date(2023, 1, 4), 150.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert [b.date for b in result] == [b.date for b in expected]
    assert [b.value for b in result] == [b.value for b in expected]


def test_balance_series_mul_scalar():
    mock_value = Mock(return_value=100.0)
    series = BalanceSeries(series=[Balance(datetime.date(2023, 1, 1), mock_value)])
    result = series * 2.5
    expected = [
        Balance(datetime.date(2023, 1, 1), 250.0),
    ]
    mock_value.assert_not_called()
    assert list(result) == expected


def test_balance_series_mul_invalid_type():
    mock_value = Mock(return_value=100.0)
    balances = [Balance(datetime.date(2023, 1, 1), mock_value)]
    series = BalanceSeries(series=balances)

    with pytest.raises(TypeError, match="Cannot multiply"):
        series * "invalid"  # type: ignore
    mock_value.assert_not_called()


def test_balance_series_truediv_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=2.0)
    mock_value4 = Mock(return_value=4.0)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 2), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 1), mock_value3),
        Balance(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 / series2
    result = list(result_series)

    expected = [
        Balance(datetime.date(2023, 1, 1), 50.0),
        Balance(datetime.date(2023, 1, 2), 50.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert result == expected


def test_balance_series_truediv_different_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=400.0)
    mock_value3 = Mock(return_value=2.0)
    mock_value4 = Mock(return_value=5.0)
    balances1 = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 3), mock_value2),
    ]
    balances2 = [
        Balance(datetime.date(2023, 1, 2), mock_value3),
        Balance(datetime.date(2023, 1, 4), mock_value4),
    ]
    series1 = BalanceSeries(series=balances1)
    series2 = BalanceSeries(series=balances2)

    result_series = series1 / series2
    result = list(result_series)

    # Note: Division by zero where no previous value exists results in inf
    expected_dates = [
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 3),
        datetime.date(2023, 1, 4),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert [b.date for b in result] == expected_dates
    # First balance: 100/0 = inf, second: 100/2 = 50, third: 400/2 = 200, fourth: 400/5 = 80
    values = [b for b in result]

    with pytest.raises(ZeroDivisionError):
        assert values[0].value
    assert values[1].value == 50.0  # 100/2
    assert values[2].value == 200.0  # 400/2
    assert values[3].value == 80.0  # 400/5


def test_balance_series_truediv_scalar():
    mock_value = Mock(return_value=100.0)
    series = BalanceSeries(series=[Balance(datetime.date(2023, 1, 1), mock_value)])
    result = series / 4.0
    expected = [
        Balance(datetime.date(2023, 1, 1), 25.0),
    ]
    mock_value.assert_not_called()
    assert list(result) == expected


def test_balance_series_truediv_invalid_type():
    mock_value = Mock(return_value=100.0)
    balances = [Balance(datetime.date(2023, 1, 1), mock_value)]
    series = BalanceSeries(series=balances)

    with pytest.raises(TypeError, match="Cannot divide"):
        series / "invalid"  # type: ignore
    mock_value.assert_not_called()


def test_balance_series_avg_period_before_series_starts():
    """Test avg when the period is entirely before the series starts."""
    balances = [
        Balance(datetime.date(2023, 1, 10), 100.0),
        Balance(datetime.date(2023, 1, 15), 200.0),
    ]
    series = BalanceSeries(series=balances)
    
    result = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 5), YF.actual360)
    assert result == 0.0


def test_balance_series_avg_period_after_series_ends():
    """Test avg when the period is entirely after the series ends."""
    balances = [
        Balance(datetime.date(2023, 1, 10), 100.0),
        Balance(datetime.date(2023, 1, 15), 200.0),
    ]
    series = BalanceSeries(series=balances)
    
    result = series.avg(datetime.date(2023, 1, 20), datetime.date(2023, 1, 25), YF.actual360)
    assert result == 200.0


def test_balance_series_avg_dates_on_balance_dates():
    """Test avg when start and end dates are exactly on balance dates."""
    balances = [
        Balance(datetime.date(2023, 1, 1), 100.0),
        Balance(datetime.date(2023, 1, 10), 200.0),
        Balance(datetime.date(2023, 1, 20), 300.0),
    ]
    series = BalanceSeries(series=balances)
    
    # Period from balance date to balance date
    result = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 10), YF.actual360)
    expected = 100.0  # Constant 100 for the entire period
    assert result == pytest.approx(expected)

    # Period spanning multiple balance dates
    result = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 20), YF.actual360)
    # 100 for 9 days, 200 for 10 days out of 19 days total
    days_100 = 9
    days_200 = 10
    total_days = 19
    expected = (100.0 * days_100 + 200.0 * days_200) / total_days
    assert result == expected


def test_balance_series_avg_dates_between_balance_dates():
    """Test avg when dates fall between balance dates."""
    balances = [
        Balance(datetime.date(2023, 1, 1), 100.0),
        Balance(datetime.date(2023, 1, 10), 200.0),
        Balance(datetime.date(2023, 1, 20), 300.0),
    ]
    series = BalanceSeries(series=balances)
    
    # Period between balance dates - should use interpolated values
    result = series.avg(datetime.date(2023, 1, 5), datetime.date(2023, 1, 15), YF.actual360)
    # From day 5-10: balance is 100, from day 10-15: balance is 200
    days_100 = 5  # Jan 5-10
    days_200 = 5  # Jan 10-15
    total_days = 10
    expected = (100.0 * days_100 + 200.0 * days_200) / total_days
    assert result == pytest.approx(expected)


def test_balance_series_avg_partial_overlap_start():
    """Test avg when period starts before series but ends within series."""
    balances = [
        Balance(datetime.date(2023, 1, 10), 100.0),
        Balance(datetime.date(2023, 1, 20), 200.0),
    ]
    series = BalanceSeries(series=balances)
    
    # Period starts before series, ends within series
    result = series.avg(datetime.date(2023, 1, 5), datetime.date(2023, 1, 15), YF.actual360)
    # From day 5-10: balance is 0, from day 10-15: balance is 100
    days_0 = 5    # Jan 5-10
    days_100 = 5  # Jan 10-15
    total_days = 10
    expected = (0.0 * days_0 + 100.0 * days_100) / total_days
    assert result == pytest.approx(expected)


def test_balance_series_avg_partial_overlap_end():
    """Test avg when period starts within series but ends after series."""
    balances = [
        Balance(datetime.date(2023, 1, 10), 100.0),
        Balance(datetime.date(2023, 1, 20), 200.0),
    ]
    series = BalanceSeries(series=balances)
    
    # Period starts within series, ends after series
    result = series.avg(datetime.date(2023, 1, 15), datetime.date(2023, 1, 25), YF.actual360)
    # From day 15-20: balance is 100, from day 20-25: balance is 200
    days_100 = 5  # Jan 15-20
    days_200 = 5  # Jan 20-25
    total_days = 10
    expected = (100.0 * days_100 + 200.0 * days_200) / total_days
    assert result == pytest.approx(expected)


def test_balance_series_avg_single_balance():
    """Test avg with a series containing only one balance."""
    balances = [Balance(datetime.date(2023, 1, 10), 150.0)]
    series = BalanceSeries(series=balances)
    
    # Period entirely before the balance
    result = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 5), YF.actual360)
    assert result == 0.0
    
    # Period starting before and ending after the balance
    result = series.avg(datetime.date(2023, 1, 5), datetime.date(2023, 1, 15), YF.actual360)
    # From day 5-10: balance is 0, from day 10-15: balance is 150
    days_0 = 5    # Jan 5-10
    days_150 = 5  # Jan 10-15
    total_days = 10
    expected = (0.0 * days_0 + 150.0 * days_150) / total_days
    assert result == expected
    
    # Period entirely after the balance
    result = series.avg(datetime.date(2023, 1, 15), datetime.date(2023, 1, 20), YF.actual360)
    assert result == pytest.approx(150.0)


def test_balance_series_avg_empty_series():
    """Test avg with an empty series."""
    series = BalanceSeries(series=[])
    
    result = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 10), YF.actual360)
    assert result == 0.0


def test_balance_series_avg_zero_period():
    """Test avg with zero year fraction (same dates would raise ValueError)."""
    balances = [Balance(datetime.date(2023, 1, 10), 100.0)]
    series = BalanceSeries(series=balances)
    
    # Test with a custom year fraction function that returns 0
    def zero_yf(dt1, dt2):
        return 0.0
    
    result = series.avg(datetime.date(2023, 1, 5), datetime.date(2023, 1, 15), zero_yf)
    assert result == 0.0


def test_balance_series_avg_different_yearfrac_methods():
    """Test avg with different year fraction calculation methods."""
    balances = [
        Balance(datetime.date(2023, 1, 1), 100.0),
        Balance(datetime.date(2023, 2, 1), 200.0),
    ]
    series = BalanceSeries(series=balances)
    
    # Test with actual360
    result_actual360 = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 2, 28), YF.actual360)

    # Test with thirty360
    result_thirty360 = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 2, 28), YF.thirty360)
    
    assert result_actual360 == pytest.approx(146.551724138)
    assert result_thirty360 == pytest.approx(147.368421053)


def test_balance_series_avg_invalid_date_range():
    """Test avg raises ValueError when dt1 >= dt2."""
    balances = [Balance(datetime.date(2023, 1, 10), 100.0)]
    series = BalanceSeries(series=balances)
    
    # dt1 > dt2
    with pytest.raises(ValueError, match="dt1 .* must be before dt2"):
        series.avg(datetime.date(2023, 1, 15), datetime.date(2023, 1, 10), YF.actual360)
    
    # dt1 == dt2
    with pytest.raises(ValueError, match="dt1 .* must be before dt2"):
        series.avg(datetime.date(2023, 1, 10), datetime.date(2023, 1, 10), YF.actual360)


def test_balance_series_avg_complex_overlap():
    """Test avg with complex overlapping scenarios."""
    balances = [
        Balance(datetime.date(2023, 1, 5), 50.0),
        Balance(datetime.date(2023, 1, 10), 100.0),
        Balance(datetime.date(2023, 1, 15), 150.0),
        Balance(datetime.date(2023, 1, 20), 200.0),
    ]
    series = BalanceSeries(series=balances)
    
    # Test period that spans multiple balance changes
    result = series.avg(datetime.date(2023, 1, 8), datetime.date(2023, 1, 18), YF.actual360)
    # From day 8-10: balance is 50 (2 days)
    # From day 10-15: balance is 100 (5 days)
    # From day 15-18: balance is 150 (3 days)
    total_days = 10
    expected = (50.0 * 2 + 100.0 * 5 + 150.0 * 3) / total_days
    assert result == pytest.approx(expected)


def test_balance_series_avg_with_lazy_evaluation():
    """Test that avg works correctly with lazy evaluation (Mock functions)."""
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    balances = [
        Balance(datetime.date(2023, 1, 1), mock_value1),
        Balance(datetime.date(2023, 1, 10), mock_value2),
    ]
    series = BalanceSeries(series=balances)
    
    result = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 10), YF.actual360)
    assert result == 100.0
    
    # The mock functions should be called when avg accesses the balance values
    mock_value1.assert_called_once()
    mock_value2.assert_not_called()  # Not needed for this specific calculation

def test_balance_series_avg_max_date_query_equal():
    """Test that avg doesn't pull balances from after the first matching balance date."""
    value_2 = Mock(return_value=200.0)
    value_3 = Mock(return_value=300.0)

    balances = (bal for bal in (
        Balance(datetime.date(2023, 1, 1), 100.0),
        Balance(datetime.date(2023, 1, 10), value_2),
        Balance(datetime.date(2023, 1, 20), value_3),
    ))
    series = BalanceSeries(series=balances)

    _ = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 10), YF.actual360)
    value_2.assert_not_called()
    value_3.assert_not_called()
    assert next(balances) == Balance(datetime.date(2023, 1, 20), 300.0)

def test_balance_series_avg_max_date_query_mid():
    """Test that avg doesn't pull balances from after the first balance after dt."""
    value_2 = Mock(return_value=200.0)
    value_3 = Mock(return_value=300.0)

    balances = (bal for bal in (
        Balance(datetime.date(2023, 1, 1), 100.0),
        Balance(datetime.date(2023, 1, 10), value_2),
        Balance(datetime.date(2023, 1, 20), value_3),
    ))
    series = BalanceSeries(series=balances)

    _ = series.avg(datetime.date(2023, 1, 1), datetime.date(2023, 1, 5), YF.actual360)
    value_2.assert_not_called()
    value_3.assert_not_called()
    assert next(balances) == Balance(datetime.date(2023, 1, 20), 300.0)
