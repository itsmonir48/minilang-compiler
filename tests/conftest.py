"""Shared pytest setup.

Golden-file tests: `golden("name", text)` compares `text` with tests/expected/name.txt.
Run `pytest --update-golden` to (re)write the expected files after an intended change,
then check the diff with `git diff tests/expected` before committing.
"""

from pathlib import Path

import pytest

EXPECTED_DIR = Path(__file__).parent / "expected"


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="rewrite tests/expected/*.txt with the current output",
    )


@pytest.fixture
def golden(request):
    update = request.config.getoption("--update-golden")

    def check(name: str, actual: str) -> None:
        path = EXPECTED_DIR / f"{name}.txt"
        if update:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(actual, encoding="utf-8")
            return
        if not path.exists():
            pytest.fail(f"missing golden file {path}; run pytest --update-golden")
        assert actual == path.read_text(encoding="utf-8")

    return check
