# Test that mypy typechecking passes for all files in /typechecking/testcode

import pathlib
import subprocess

import pytest

config_path = pathlib.Path(__file__).parent / "pyproject.toml"


# Type check src
src_path = pathlib.Path(__file__).parent.parent.parent / "src"


def test_src_mypy():
    assert run_mypy(src_path).returncode == 0, f"Mypy failed for {src_path}"


# Type check usage tests code

python_test_code_files = [
    file
    for file in (pathlib.Path(__file__).parent / "testcode").iterdir()
    if file.is_file() and file.suffix == ".py"
]


@pytest.mark.parametrize("test_file", python_test_code_files)
def test_mypy_typechecking(test_file: pathlib.Path):
    assert run_mypy(test_file).returncode == 0


def run_mypy(file):
    return subprocess.run(
        [
            "uv",
            "run",
            "mypy",
            "--cache-dir=/dev/null",
            "--config-file",
            config_path,
            file,
        ],
        capture_output=True,
    )


if __name__ == "__main__":
    # Run mypy for all files in /typechecking/testcode
    for file in python_test_code_files:
        run_mypy(file)
