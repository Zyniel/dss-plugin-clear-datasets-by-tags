"""The opt-in of the screenshot tests, and their browser: they take the README screenshots on the test DSS.

They use the fixtures of the integration tests: see tests/integration/fixtures.py. They run only when pytest gets
--screenshots, even when DSS_INTEGRATION_CONFIG is set, so that running the tests never rewrites the README images.
With the option, they are still skipped without a config file, like the integration tests.

Without the option, pytest still imports the test files of this folder. Import the dependencies of the screenshots
inside the tests, or with pytest.importorskip(): the CI does not install them.
"""

from collections.abc import Iterator
from typing import Any, NamedTuple

import pytest

from screenshots import dss_ui
from screenshots.images import SCALE


class UiLogin(NamedTuple):
    """The login and the password of the DSS UI, from the config file."""

    login: str
    password: str


@pytest.fixture(scope="session", autouse=True)
def skip_without_screenshots_option(pytestconfig: pytest.Config) -> None:
    """Skip the screenshot tests unless pytest gets --screenshots.

    An autouse fixture runs first within its scope, and session is the widest one: without the option, a screenshot
    test reads no config file and never reaches the DSS.
    """
    if not pytestconfig.getoption("screenshots"):
        pytest.skip("Screenshot tests: run pytest with --screenshots. They can rewrite the README images.")


@pytest.fixture(scope="session")
def ui_login(config: dict[str, Any]) -> UiLogin:
    """Return the UI login of the config file, or stop the tests when it is missing."""
    login, password = config.get("ui_login"), config.get("ui_password")
    if not login or not password:
        pytest.fail(
            'The config file has no UI login. Add "ui_login": "admin" and "ui_password": "<password of admin>": '
            "see docs/screenshots.md.",
            pytrace=False,
        )
    return UiLogin(login, password)


@pytest.fixture(scope="session")
def browser() -> Iterator[Any]:
    """Return the Chromium of Playwright, or skip the tests without the screenshots dependency group.

    A session fixture, so that a missing group skips the tests before the plugin is installed on the DSS.
    """
    sync_api = pytest.importorskip(
        "playwright.sync_api", reason="Screenshot tests: run them with `uv run --group screenshots`."
    )
    with sync_api.sync_playwright() as playwright:
        yield playwright.chromium.launch()


@pytest.fixture
def dss_page(config: dict[str, Any], ui_login: UiLogin, browser: Any) -> Iterator[Any]:
    """Return a page of Chromium, logged in to the DSS UI: in English, in the light theme, at scale 2."""
    context = browser.new_context(
        base_url=config["url"],
        locale="en-US",
        color_scheme="light",
        device_scale_factor=SCALE,
        viewport=dss_ui.WINDOW_SIZE,
    )
    try:
        page = context.new_page()
        dss_ui.log_in(page, ui_login.login, ui_login.password)
        yield page
    finally:
        context.close()
