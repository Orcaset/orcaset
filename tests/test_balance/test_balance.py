import datetime
from unittest.mock import Mock

import pytest

from orcaset.financial.balance_node import Balance


def test_balance_init_with_value():
    date = datetime.date(2023, 1, 1)
    balance = Balance(date, 100.0)
    assert balance.date == date
    assert balance.value == 100.0

def test_balance_init_with_callable():
    date = datetime.date(2023, 1, 1)
    mock_func = Mock(return_value=200.0)
    balance = Balance(date, mock_func)

    assert balance.date == date
    mock_func.assert_not_called()

    # First access should call the function
    assert balance.value == 200.0
    mock_func.assert_called_once()

    # Second access should use cached value
    assert balance.value == 200.0
    mock_func.assert_called_once()

def test_balance_init_with_int():
    date = datetime.date(2023, 1, 1)
    balance = Balance(date, 100)
    assert balance.value == 100

def test_balance_add():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    result = balance + 50.0
    assert result.date == balance.date
    assert result.value == 150.0

def test_balance_radd():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    result = 50.0 + balance
    assert result.date == balance.date
    assert result.value == 150.0

def test_balance_add_invalid_type():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot add"):
        balance + "invalid"  # type: ignore

def test_balance_sub():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    result = balance - 30.0
    assert result.date == balance.date
    assert result.value == 70.0

def test_balance_sub_invalid_type():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot subtract"):
        balance - "invalid"  # type: ignore

def test_balance_mul():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    result = balance * 2.0
    assert result.date == balance.date
    assert result.value == 200.0

def test_balance_rmul():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    result = 2.0 * balance
    assert result.date == balance.date
    assert result.value == 200.0

def test_balance_mul_invalid_type():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot multiply"):
        balance * "invalid"  # type: ignore

def test_balance_truediv():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    result = balance / 2.0
    assert result.date == balance.date
    assert result.value == 50.0

def test_balance_truediv_invalid_type():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    with pytest.raises(TypeError, match="Cannot divide"):
        balance / "invalid"  # type: ignore

def test_balance_neg():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    result = -balance
    assert result.date == balance.date
    assert result.value == -100.0

def test_balance_eq_same_values():
    date = datetime.date(2023, 1, 1)
    balance1 = Balance(date, 100.0)
    balance2 = Balance(date, 100.0)
    assert balance1 == balance2

def test_balance_eq_different_dates():
    balance1 = Balance(datetime.date(2023, 1, 1), 100.0)
    balance2 = Balance(datetime.date(2023, 1, 2), 100.0)
    assert balance1 != balance2

def test_balance_eq_different_values():
    date = datetime.date(2023, 1, 1)
    balance1 = Balance(date, 100.0)
    balance2 = Balance(date, 200.0)
    assert balance1 != balance2

def test_balance_eq_with_callable():
    date = datetime.date(2023, 1, 1)
    balance1 = Balance(date, lambda: 100.0)
    balance2 = Balance(date, 100.0)
    assert balance1 == balance2

def test_balance_eq_different_type():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    assert balance != "not a balance"

def test_balance_repr_with_value():
    balance = Balance(datetime.date(2023, 1, 1), 100.0)
    repr_str = repr(balance)
    assert "Balance(date=2023-01-01, value=100.0)" == repr_str

def test_balance_repr_with_callable():
    balance = Balance(datetime.date(2023, 1, 1), lambda: 100.0)
    repr_str = repr(balance)
    assert "Balance(date=2023-01-01, value=<unevaluated>)" == repr_str

def test_balance_repr_after_evaluation():
    balance = Balance(datetime.date(2023, 1, 1), lambda: 100.0)
    _ = balance.value  # Force evaluation
    repr_str = repr(balance)
    assert "Balance(date=2023-01-01, value=100.0)" == repr_str

def test_balance_add_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    balance = Balance(datetime.date(2023, 1, 1), mock_func)
    
    result = balance + 50.0
    mock_func.assert_not_called()
    
    assert result.value == 150.0
    mock_func.assert_called_once()

def test_balance_radd_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    balance = Balance(datetime.date(2023, 1, 1), mock_func)
    
    result = 50.0 + balance
    mock_func.assert_not_called()
    
    assert result.value == 150.0
    mock_func.assert_called_once()

def test_balance_sub_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    balance = Balance(datetime.date(2023, 1, 1), mock_func)
    
    result = balance - 30.0
    mock_func.assert_not_called()
    
    assert result.value == 70.0
    mock_func.assert_called_once()

def test_balance_mul_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    balance = Balance(datetime.date(2023, 1, 1), mock_func)
    
    result = balance * 2.0
    mock_func.assert_not_called()
    
    assert result.value == 200.0
    mock_func.assert_called_once()

def test_balance_rmul_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    balance = Balance(datetime.date(2023, 1, 1), mock_func)
    
    result = 2.0 * balance
    mock_func.assert_not_called()
    
    assert result.value == 200.0
    mock_func.assert_called_once()

def test_balance_truediv_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    balance = Balance(datetime.date(2023, 1, 1), mock_func)
    
    result = balance / 2.0
    mock_func.assert_not_called()
    
    assert result.value == 50.0
    mock_func.assert_called_once()

def test_balance_neg_lazy_evaluation():
    mock_func = Mock(return_value=100.0)
    balance = Balance(datetime.date(2023, 1, 1), mock_func)
    
    result = -balance
    mock_func.assert_not_called()
    
    assert result.value == -100.0
    mock_func.assert_called_once()

def test_balance_eq_lazy_evaluation():
    mock_func1 = Mock(return_value=100.0)
    mock_func2 = Mock(return_value=100.0)
    
    date = datetime.date(2023, 1, 1)
    balance1 = Balance(date, mock_func1)
    balance2 = Balance(date, mock_func2)
    
    # Equality comparison should evaluate both functions
    result = balance1 == balance2
    assert result is True
    mock_func1.assert_called_once()
    mock_func2.assert_called_once()
