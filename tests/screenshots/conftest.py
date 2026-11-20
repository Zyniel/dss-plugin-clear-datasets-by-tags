"""The opt-in of the screenshot tests: they take the README screenshots on the test DSS of the integration tests.

They use the fixtures of the integration tests: see tests/integration/fixtures.py. They run only when pytest gets
--screenshots, even when DSS_INTEGRATION_CONFIG is set, so that running the tests never rewrites the README images.
With the option, they are still skipped without a config file, like the integration tests.

Without the option, pytest still imports the test files of this folder. Import the dependencies of the screenshots
inside the tests, or with pytest.importorskip(): the CI does not install them.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def skip_without_screenshots_option(pytestconfig: pytest.Config) -> None:
    """Skip the screenshot tests unless pytest gets --screenshots.

    An autouse fixture runs first within its scope, and session is the widest one: without the option, a screenshot
    test reads no config file and never reaches the DSS.
    """
    if not pytestconfig.getoption("screenshots"):
        pytest.skip("Screenshot tests: run pytest with --screenshots. They can rewrite the README images.")
