import datetime
from unittest.mock import Mock

import pytest

from orcaset.financial.balance_node import Balance, BalanceSeries


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
