import datetime
from unittest.mock import Mock

import pytest

from orcaset.financial.payment_node import Payment


def test_payment_init_with_value():
    date = datetime.date(2023, 1, 1)
    payment = Payment(date, 100.0)
    assert payment.date == date
    assert payment.value == 100.0


def test_payment_init_with_callable():
    date = datetime.date(2023, 1, 1)
    mock_func = Mock(return_value=200.0)
    payment = Payment(date, mock_func)

    assert payment.date == date
    mock_func.assert_not_called()

    # First access should call the function
    assert payment.value == 200.0
    mock_func.assert_called_once()

    # Second access should use cached value
    assert payment.value == 200.0
    mock_func.assert_called_once()


def test_payment_init_with_int():
    date = datetime.date(2023, 1, 1)
    payment = Payment(date, 100)
    assert payment.value == 100


def test_payment_add():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    result = payment + 50.0
    assert result.date == payment.date
    assert result.value == 150.0


def test_payment_radd():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    result = 50.0 + payment
    assert result.date == payment.date
    assert result.value == 150.0


def test_payment_add_invalid_type():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot add.*Only float or int is allowed"):
        payment + "invalid"  # type: ignore


def test_payment_sub():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    result = payment - 30.0
    assert result.date == payment.date
    assert result.value == 70.0


def test_payment_sub_invalid_type():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot subtract.*Only float or int is allowed"):
        payment - "invalid"  # type: ignore


def test_payment_mul():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    result = payment * 2.0
    assert result.date == payment.date
    assert result.value == 200.0


def test_payment_rmul():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    result = 2.0 * payment
    assert result.date == payment.date
    assert result.value == 200.0


def test_payment_mul_invalid_type():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot multiply.*Only float or int is allowed"):
        payment * "invalid"  # type: ignore


def test_payment_truediv():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    result = payment / 2.0
    assert result.date == payment.date
    assert result.value == 50.0


def test_payment_truediv_invalid_type():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot divide.*Only float or int is allowed"):
        payment / "invalid"  # type: ignore


def test_payment_neg():
    payment = Payment(datetime.date(2023, 1, 1), 100.0)
    result = -payment
    assert result.date == payment.date
    assert result.value == -100.0


def test_payment_add_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    payment = Payment(datetime.date(2023, 1, 1), mock_func)

    result = payment + 50.0
    mock_func.assert_not_called()
    
    assert result.value == 150.0
    mock_func.assert_called_once()

def test_payment_radd_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    payment = Payment(datetime.date(2023, 1, 1), mock_func)
    
    result = 50.0 + payment
    mock_func.assert_not_called()
    
    assert result.value == 150.0
    mock_func.assert_called_once()

def test_payment_sub_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    payment = Payment(datetime.date(2023, 1, 1), mock_func)
    
    result = payment - 30.0
    mock_func.assert_not_called()
    
    assert result.value == 70.0
    mock_func.assert_called_once()

def test_payment_mul_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    payment = Payment(datetime.date(2023, 1, 1), mock_func)

    result = payment * 2.0
    mock_func.assert_not_called()

    assert result.value == 200.0
    mock_func.assert_called_once()

def test_payment_rmul_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    payment = Payment(datetime.date(2023, 1, 1), mock_func)
    
    result = 2.0 * payment
    mock_func.assert_not_called()
    
    assert result.value == 200.0
    mock_func.assert_called_once()

def test_payment_truediv_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    payment = Payment(datetime.date(2023, 1, 1), mock_func)
    
    result = payment / 2.0
    mock_func.assert_not_called()
    
    assert result.value == 50.0
    mock_func.assert_called_once()

def test_payment_neg_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    payment = Payment(datetime.date(2023, 1, 1), mock_func)
    
    result = -payment
    mock_func.assert_not_called()
    
    assert result.value == -100.0
    mock_func.assert_called_once()
