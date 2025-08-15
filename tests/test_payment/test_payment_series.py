import datetime
from unittest.mock import Mock

import pytest

from orcaset.financial.payment_node import Payment, PaymentSeries


def test_payment_series_creation():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)
    result = list(series)
    assert result == payments
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()


def test_payment_series_iter_cache():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)

    result1 = [p for p in series]
    result2 = [p for p in series]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    for r1, r2 in zip(result1, result2):
        assert r1 is r2


def test_payment_series_on_existing_date():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 3), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)
    assert series.on(datetime.date(2023, 1, 1)) == 100.0
    assert series.on(datetime.date(2023, 1, 3)) == 300.0


def test_payment_series_on_missing_date():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 3), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)
    assert series.on(datetime.date(2023, 1, 2)) == 0
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()


def test_payment_series_over_inclusive_period():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=300.0)
    mock_value4 = Mock(return_value=500.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
        Payment(datetime.date(2023, 1, 3), mock_value3),
        Payment(datetime.date(2023, 1, 5), mock_value4),
    ]
    series = PaymentSeries(payment_series=payments)
    # From 2023-01-01 (exclusive) to 2023-01-03 (inclusive)
    total = series.over(datetime.date(2023, 1, 1), datetime.date(2023, 1, 3))
    assert total == 500.0  # 200 + 300 (100 is excluded because from_date is exclusive)
    mock_value4.assert_not_called()


def test_payment_series_over_no_payments():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=500.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 5), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)
    # No payments between 2023-01-02 and 2023-01-04
    total = series.over(datetime.date(2023, 1, 2), datetime.date(2023, 1, 4))
    assert total == 0
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()


def test_payment_series_over_edge_case_same_date():
    mock_value = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 2), mock_value),
    ]
    series = PaymentSeries(payment_series=payments)
    # From 2023-01-01 to 2023-01-02 should include payment on 2023-01-02
    total = series.over(datetime.date(2023, 1, 1), datetime.date(2023, 1, 2))
    assert total == 200.0


def test_payment_series_after():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=300.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
        Payment(datetime.date(2023, 1, 3), mock_value3),
    ]
    series = PaymentSeries(payment_series=payments)
    after_series = series.after(datetime.date(2023, 1, 1))
    result = list(after_series)

    expected = [
        Payment(datetime.date(2023, 1, 2), mock_value2),
        Payment(datetime.date(2023, 1, 3), mock_value3),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    assert result == expected


def test_payment_series_sub_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=50.0)
    mock_value4 = Mock(return_value=75.0)
    payments1 = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    payments2 = [
        Payment(datetime.date(2023, 1, 1), mock_value3),
        Payment(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = PaymentSeries(payment_series=payments1)
    series2 = PaymentSeries(payment_series=payments2)

    result_series = series1 - series2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 50.0),
        Payment(datetime.date(2023, 1, 2), 125.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_sub_different_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    mock_value3 = Mock(return_value=200.0)
    payments1 = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 3), mock_value2),
    ]
    payments2 = [
        Payment(datetime.date(2023, 1, 2), mock_value3),
    ]
    series1 = PaymentSeries(payment_series=payments1)
    series2 = PaymentSeries(payment_series=payments2)

    result_series = series1 - series2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 100.0),
        Payment(datetime.date(2023, 1, 2), 200.0),
        Payment(datetime.date(2023, 1, 3), 300.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_mul_same_dates():
    mock_value1 = Mock(return_value=10.0)
    mock_value2 = Mock(return_value=20.0)
    mock_value3 = Mock(return_value=2.0)
    mock_value4 = Mock(return_value=3.0)
    payments1 = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    payments2 = [
        Payment(datetime.date(2023, 1, 1), mock_value3),
        Payment(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = PaymentSeries(payment_series=payments1)
    series2 = PaymentSeries(payment_series=payments2)

    result_series = series1 * series2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 20.0),
        Payment(datetime.date(2023, 1, 2), 60.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_truediv_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=2.0)
    mock_value4 = Mock(return_value=4.0)
    payments1 = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    payments2 = [
        Payment(datetime.date(2023, 1, 1), mock_value3),
        Payment(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = PaymentSeries(payment_series=payments1)
    series2 = PaymentSeries(payment_series=payments2)

    result_series = series1 / series2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 50.0),
        Payment(datetime.date(2023, 1, 2), 50.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_sub_invalid_type():
    mock_value = Mock(return_value=100.0)
    payments = [Payment(datetime.date(2023, 1, 1), mock_value)]
    series = PaymentSeries(payment_series=payments)

    with pytest.raises(TypeError, match="Cannot subtract"):
        series - "invalid"  # type: ignore


def test_payment_series_mul_invalid_type():
    mock_value = Mock(return_value=100.0)
    payments = [Payment(datetime.date(2023, 1, 1), mock_value)]
    series = PaymentSeries(payment_series=payments)

    with pytest.raises(TypeError, match="Cannot multiply"):
        series * "invalid"  # type: ignore


def test_payment_series_truediv_invalid_type():
    mock_value = Mock(return_value=100.0)
    payments = [Payment(datetime.date(2023, 1, 1), mock_value)]
    series = PaymentSeries(payment_series=payments)

    with pytest.raises(TypeError, match="Cannot divide"):
        series / "invalid"  # type: ignore


def test_payment_series_add_same_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    mock_value3 = Mock(return_value=50.0)
    mock_value4 = Mock(return_value=75.0)
    payments1 = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    payments2 = [
        Payment(datetime.date(2023, 1, 1), mock_value3),
        Payment(datetime.date(2023, 1, 2), mock_value4),
    ]
    series1 = PaymentSeries(payment_series=payments1)
    series2 = PaymentSeries(payment_series=payments2)

    result_series = series1 + series2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 150.0),
        Payment(datetime.date(2023, 1, 2), 275.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert result == expected


def test_payment_series_add_different_dates():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=300.0)
    mock_value3 = Mock(return_value=200.0)
    mock_value4 = Mock(return_value=400.0)
    payments1 = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 3), mock_value2),
    ]
    payments2 = [
        Payment(datetime.date(2023, 1, 2), mock_value3),
        Payment(datetime.date(2023, 1, 4), mock_value4),
    ]
    series1 = PaymentSeries(payment_series=payments1)
    series2 = PaymentSeries(payment_series=payments2)

    result_series = series1 + series2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 100.0),
        Payment(datetime.date(2023, 1, 2), 200.0),
        Payment(datetime.date(2023, 1, 3), 300.0),
        Payment(datetime.date(2023, 1, 4), 400.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    mock_value3.assert_not_called()
    mock_value4.assert_not_called()
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_add_with_lazy_evaluation():
    payments1 = [Payment(datetime.date(2023, 1, 1), lambda: 100.0)]
    payments2 = [Payment(datetime.date(2023, 1, 1), lambda: 50.0)]
    series1 = PaymentSeries(payment_series=payments1)
    series2 = PaymentSeries(payment_series=payments2)

    result_series = series1 + series2
    result = list(result_series)

    assert len(result) == 1
    assert result[0].date == datetime.date(2023, 1, 1)
    assert result[0].value == 150.0


def test_payment_series_add_invalid_type():
    mock_value = Mock(return_value=100.0)
    payments = [Payment(datetime.date(2023, 1, 1), mock_value)]
    series = PaymentSeries(payment_series=payments)

    with pytest.raises(TypeError, match="Cannot add"):
        series + "invalid"  # type: ignore
    mock_value.assert_not_called()


def test_payment_series_neg():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=-200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)
    neg_series = -series
    result = list(neg_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), -100.0),
        Payment(datetime.date(2023, 1, 2), 200.0),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    assert result == expected


def test_payment_series_empty():
    series = PaymentSeries(payment_series=[])
    assert list(series) == []
    assert series.on(datetime.date(2023, 1, 1)) == 0
    assert series.over(datetime.date(2023, 1, 1), datetime.date(2023, 1, 3)) == 0


def test_payment_series_single_payment():
    mock_value = Mock(return_value=150.0)
    payment = Payment(datetime.date(2023, 1, 2), mock_value)
    series = PaymentSeries(payment_series=[payment])

    assert series.on(datetime.date(2023, 1, 2)) == 150.0
    assert series.on(datetime.date(2023, 1, 1)) == 0
    assert series.over(datetime.date(2023, 1, 1), datetime.date(2023, 1, 2)) == 150.0
    assert series.over(datetime.date(2023, 1, 2), datetime.date(2023, 1, 3)) == 0


def test_payment_series_iter_with_generator():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    def payment_generator():
        yield Payment(datetime.date(2023, 1, 1), mock_value1)
        yield Payment(datetime.date(2023, 1, 2), mock_value2)

    series = PaymentSeries(payment_series=payment_generator())
    result = list(series)

    expected = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    mock_value1.assert_not_called()
    mock_value2.assert_not_called()
    assert result == expected


def test_payment_series_add_scalar():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)

    result_series = series + 50
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 150.0),
        Payment(datetime.date(2023, 1, 2), 250.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_radd_scalar():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)

    result_series = 50 + series
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 150.0),
        Payment(datetime.date(2023, 1, 2), 250.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_sub_scalar():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)

    result_series = series - 25
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 75.0),
        Payment(datetime.date(2023, 1, 2), 175.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_mul_scalar():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)

    result_series = series * 2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 200.0),
        Payment(datetime.date(2023, 1, 2), 400.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_rmul_scalar():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)

    result_series = 3 * series
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 300.0),
        Payment(datetime.date(2023, 1, 2), 600.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_truediv_scalar():
    mock_value1 = Mock(return_value=100.0)
    mock_value2 = Mock(return_value=200.0)
    payments = [
        Payment(datetime.date(2023, 1, 1), mock_value1),
        Payment(datetime.date(2023, 1, 2), mock_value2),
    ]
    series = PaymentSeries(payment_series=payments)

    result_series = series / 2
    result = list(result_series)

    expected = [
        Payment(datetime.date(2023, 1, 1), 50.0),
        Payment(datetime.date(2023, 1, 2), 100.0),
    ]
    assert [p.date for p in result] == [p.date for p in expected]
    assert [p.value for p in result] == [p.value for p in expected]


def test_payment_series_scalar_operations_with_float():
    mock_value = Mock(return_value=100.0)
    payments = [Payment(datetime.date(2023, 1, 1), mock_value)]
    series = PaymentSeries(payment_series=payments)

    add_result = list(series + 50.5)
    sub_result = list(series - 25.5)
    mul_result = list(series * 1.5)
    div_result = list(series / 2.0)

    assert add_result[0].value == 150.5
    assert sub_result[0].value == 74.5
    assert mul_result[0].value == 150.0
    assert div_result[0].value == 50.0
