# Testing Type Hints

`orcaset` is primarily written with [Pyright](https://github.com/microsoft/pyright) in mind based on its comprehensive coverage scope and broad language server use, but the test suite includes type checking against both Pyright and [Mypy](https://mypy.readthedocs.io/en/stable/index.html). Pyright (correctly) accepts more compatible parent type parameters, so using Mypy may cause false negative type checking errors.

Type hint test code is in `/testcode`. Pyright and Mypy configurations for testing are included in the `pyproject.toml`. The test code includes cases that are expected to pass as well as cases that are expect to fail. Failure cases are noted inline with `# type: ignore[mypy-error]  # pyright: ignore[pyrightError]` with Pyright and Mypy both configured to raise errors for any unnecessary type ignore comments.

Other than the flag for raising unnecessary ignores for testing purposes as describe in the preceding paragraph, the only other flags are for specifying Python 3.13 and requiring all generics be fully defined (either explicitly or implicitly through a type default). While not strictly required, unknown types are treated as `Any` which can cause the type checker to pass when the type parameter has an upper bound that isn't actually satisfied. Enforcing fully defined types avoids these errors.

Pyright includes the `enableTypeIgnoreComments = false` so that Pyright specific ignores can be separated inline from Mypy ignores. Mypy requires ignores in some places Pyright does not.

Pyright and Mypy are run as subprocesses from `pytest` wrappers. This means that:

1. Static typing failures will show up in the `pytest` report,
2. `node` and `npm` must be installed in order to run the Pyright tests, and
3. `mypy` must be installed in the active Python environment (it is included as a dev dependency)
