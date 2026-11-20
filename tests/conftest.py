"""The setup of pytest for all the tests: the fixtures of a real DSS, and the option of the screenshot tests.

pytest takes pytest plugins and command-line options only from the conftest.py files it loads at startup. This one,
at the root of the tests, is always among them, so both are here.
"""

import pytest

# The fixtures of the integration tests, for every test folder.
pytest_plugins = ["integration.fixtures"]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --screenshots: without it, tests/screenshots/conftest.py skips the screenshot tests."""
    parser.addoption(
        "--screenshots",
        action="store_true",
        help="Run the screenshot tests of tests/screenshots, on the DSS of DSS_INTEGRATION_CONFIG.",
    )
