# Orcaset - Financial modeling framework for Python

Orcaset is a financial modeling framework for Python. It brings Python's rich ecosystem of data management, networking, and statistical capabilities to financial analysis. Its open design enables flexible data ingestion and the ability to run anywhere. By using AI code generation tools, users can automate analyses and decrease time between question and insight.

Orcaset natively integrates with Python's first-class data management tools.

- **Direct Ingestion** - Fetch and parse from any web API, database, or document.
- **Cleansing & Manipulation** - Transform large data sets. Easily apply complex pivots or mathematical operations.

Orcaset inherits the benefits of industry-standard tooling and programming best practices.

- **Model Automation** - Develop analyses quickly with AI-assisted coding tools. Programmatically rerun results when assumptions change.
- **Error Safety** - Static type hints and test suites alert users to errors early.
- **Version Control** - Use `git` to develop an audit trail, track changes, and annotate updates.

## Install

Requires Python 3.13 or later. Install with `pip`.

```shell
pip install orcaset
```

Or add to the current project using `uv`.

```shell
uv add orcaset
```

## Quickstart

### Modeling a Line Item

Orcaset breaks financial transactions into three basic types: _accruals_ occurring over a period of time, _payments_ representing flows on a specific date, and _balances_ as of a specific date. An accrual has the following structure:

```python
class Accrual:
    period: tuple[date, date]  # Accrual period start and end dates
    value: float  # Accrual value
    yf: Callable[[date, date], float]  # Function to interpolate partial periods
```

Payments and balances signatures are even simpler, consisting of a simple `tuple[date, float]` pair.

An instance of `Accrual`, `Payment` or `Balance` is analogous to a cell in a spreadsheet. Collecting a series of "cells" together creates a row in a spreadsheet. A simple representation in Python might be a `list` of `Accrual` objects (or `Payment` or `Balance` objects). Lists work well if all the values are known ahead of time, for example, when quoting historical values. For dynamic calculations, Orcaset relies on other iterable constructs, primarily [generators](https://realpython.com/introduction-to-python-generators/).

Orcaset has built-in base classes that make it easy to define and manipulate series of "cells". Consider a line item for revenue accruals that grows at a constant annual rate. We could model this by subclassing `AccrualSeriesBase`.

```python
from dataclasses import dataclass
from datetime import date
from typing import Iterable
from dateutil.relativedelta import relativedelta
from orcaset.financial import YF, Accrual, AccrualSeriesBase, Period


class Revenue(AccrualSeriesBase):
    def _accruals(self) -> Iterable[Accrual]:
        # Initial accrual
        acc = Accrual(
            period=Period(date(2020, 12, 31), date(2021, 12, 31)),
            value=1000,
            yf=YF.thirty360
        )

        while True:
            # Yield the current accrual
            yield acc
            # Advance to the next accrual at 5% growth
            acc = Accrual(
                period=Period(acc.period.end, acc.period.end + relativedelta(years=1)),
                value=acc.value * 1.05,
                yf=YF.thirty360
            )
```

The `AccrualSeriesBase` class is an abstract base class that expects subclasses to override the `_accruals` method to yield consecutive accruals. We can get the underlying `Accrual`s by iterating over an instance of the class (note that revenue is an infinite series, so we have to manually break the loop before it overflows).

```python
revenue = Revenue()

for i, acc in enumerate(revenue):
    if i > 2:
        break
    print(f"{acc.period}: {acc.value}")
# Period(2020-12-31, 2021-12-31): 1000
# Period(2021-12-31, 2022-12-31): 1050.0
# Period(2022-12-31, 2023-12-31): 1102.5
```

We can also query the accrued amount between any two arbitrary dates. Partial periods are automatically interpolated based on the accrual's year fraction attribute.

```python
revenue.accrue(date(2023, 11, 9), date(2024, 3, 14))
# 397.20624999999995
```

We can also apply basic math operators against scalar values or other accrual series.

```python
from itertools import islice

scalar_half = revenue * 0.5

for acc in islice(scalar_half, 3):
    print(f"{acc.period}: {acc.value}")
# Period(2020-12-31, 2021-12-31): 500.0
# Period(2021-12-31, 2022-12-31): 525.0
# Period(2022-12-31, 2023-12-31): 551.25

series_double = revenue + revenue

for acc in islice(series_double, 3):
    print(f"{acc.period}: {acc.value}")
# Period(2020-12-31, 2021-12-31): 2000
# Period(2021-12-31, 2022-12-31): 2100.0
# Period(2022-12-31, 2023-12-31): 2205.0
```

The `AccrualSeriesBase` class provides other convenience functions for creating and manipulating accrual iterables. Orcaset includes `PaymentSeriesBase` and `BalanceSeriesBase` that provide similar base classes to create and manipulate iterables of payment and balance objects respectively.

### Composing Multi-Line Models

Orcaset organizes collections of series into hierarchical trees. Each node in the tree can access its parent node with the `parent` property. References to children nodes are just regular instance attributes.

Let's expand our previous model to include a line item for expenses (which will be calculated as a percent of revenue). Revenue and expense will be wrapped into an income line. The basic structure will be:

```
Income
├── Revenue
└── Expense
    └── percent_revenue
```

Notice that expense depends on the sister revenue node.

We can define classes for income and expense as:

```python
@dataclass
class Income[P = None](AccrualSeriesBase[P]):
    revenue: Revenue
    opex: "Expense[Income]"

    def _accruals(self) -> Iterable[Accrual]:
        return self.revenue + self.opex


@dataclass
class Expense[P: Income = Income](AccrualSeriesBase[P]):
    percent_revenue: float

    def _accruals(self) -> Iterable[Accrual]:
        yield from self.parent.revenue * -self.percent_revenue
```

> [!NOTE] 
> `@dataclass` automatically generates the `__init__` constructor, as well as other useful dunder methods, based on the type annotations. It isn't required, but it provides a more concise and declarative way to list model assumptions.

The `_accruals` logic to generate the series of "cells" for each class is straight forward. Income is the sum of revenue and expense. The expense class navigates the tree to find the revenue node and multiplies it by some cost margin.

The expense class doesn't care about the implementation of revenue projections, but it does require the revenue object to exist. Orcaset leverages Python's type annotations to verify model composition. Nodes within the tree are generic with respect to their parent type. In the expense class definition, `Expense[P: Income](AccrualSeriesBase[P])` tells Python that it expect to have a parent `P` bound to type `Income`. In the income class definition, `Income` is passed as the type parameter of `Expense`. If there is a type conflict between the expected and actual parent types, static type checkers such as [Pyright](https://github.com/microsoft/pyright) or [Mypy](https://mypy.readthedocs.io/en/stable/#) will raise errors.

By way of example, if we try to use `Expense` in a model with an incompatible parent type, the type error is caught immediately.

```python
from orcaset import Node

@dataclass
class BadParent[P = None](Node[P]):
    opex: "Expense[BadParent]"
# pyright error: reportInvalidTypeArguments
# mypy error: [type-var]
```

> [!NOTE] 
> `Expense[P: Income = Income]` uses syntax from [PEP 695](https://peps.python.org/pep-0695/) and [PEP 696](https://peps.python.org/pep-0696/) available starting in Python 3.13. It states that the generic type parameter `P` (which maps to the class's `parent` property) is bound to `Income` and will default to `Income` if it's ever undefined.

With the model fully built, we can now query income over time.

```python
income = Income(
    revenue=Revenue(),
    opex=Expense(percent_revenue=0.65)
)

income.accrue(date(2024, 12, 31), date(2025, 12, 31))
# 425.42718750000006
```

### Cache Management

Financial models are often highly interdependent, either directly or indirectly across other line items. In order to improve performance, `AccrualBaseSeries` caches values yielded from `_accruals` (and from `_payments` and `_balances` in the analogous `PaymentBaseSeries` and `BalanceBaseSeries` classes respectively).

```python
income.opex.accrue(date(2024, 12, 31), date(2025, 12, 31))
# -790.0790625000001

# Update the expense margin
income.opex.percent_revenue = 0.7
income.opex.accrue(date(2024, 12, 31), date(2025, 12, 31))
# -790.0790625000001  NOT UPDATED FOR THE NEW EXPENSE RATIO
```

To avoid accidentally using stale assumptions, runs should be encapsulated in a context manager. On entry to the context manager, the cache for the entire model will be cleared and a clean, deep copy of the model will be returned.

```python
with income as inc:
    inc.opex.percent_revenue = 0.7
    inc.opex.accrue(date(2025, 12, 31), date(2026, 12, 31))
    # -893.3970937500002  REFLECTS UPDATED EXPENSES AS EXPECTED
```

Alternatively, the cache can be cleared manually with `cache_clear()`.

## License

Orcaset is licensed under the Server Side Public License v1. See the LICENSE file for details.
