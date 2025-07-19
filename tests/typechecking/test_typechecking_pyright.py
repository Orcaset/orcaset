# Test that pyright typechecking passes for all files in /typechecking/testcode

import pathlib
import subprocess

import pytest


config_path = pathlib.Path(__file__).parent / "pyproject.toml"

# Type check src
src_path = pathlib.Path(__file__).parent.parent.parent / "src"


def test_src_pyright():
    assert run_pyright(src_path).returncode == 0, f"Pyright failed for {src_path}"


# Type check usage tests code
python_test_code_files = [
    file
    for file in (pathlib.Path(__file__).parent / "testcode").iterdir()
    if file.is_file() and file.suffix == ".py"
]


@pytest.mark.parametrize("test_file", python_test_code_files)
def test_pyright_typechecking(test_file: pathlib.Path):
    assert run_pyright(test_file).returncode == 0


def run_pyright(file):
    return subprocess.run(
        ["uv", "run", "pyright", "-p", config_path, file]
    )


if __name__ == "__main__":
    # Run pyright for all files in /typechecking/testcode
    for file in python_test_code_files:
        run_pyright(file)
