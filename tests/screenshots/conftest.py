"""The fixtures of the screenshot tests: their opt-in, the check of the DSS, the demo projects, and the browser.

The screenshot tests take the README screenshots on the test DSS of the integration tests, and use their fixtures:
see tests/integration/fixtures.py. They run only when pytest gets --screenshots, even when DSS_INTEGRATION_CONFIG is
set, so that running the tests never rewrites the README images. With the option, they are still skipped without a
config file, like the integration tests. A DSS that is not ready for the demo projects stops them all, before any
change.

Without the option, pytest still imports the test files of this folder. Import the dependencies of the screenshots
inside the tests, or with pytest.importorskip(): the CI does not install them.
"""

from collections.abc import Iterator
from typing import Any, Callable

import pytest

from integration.fixtures import connect
from screenshots import dss_ui
from screenshots.demo_projects import (
    DEMO_KEYS,
    DemoProjectError,
    DemoProjects,
    check_demo_key_is_free,
    check_tag_categories,
    create_demo_projects,
    delete_demo_projects,
)
from screenshots.dss_ui import UiLogin
from screenshots.images import SCALE


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


@pytest.fixture(scope="session", autouse=True)
def ready_for_demo_projects(skip_without_screenshots_option: None, config: dict[str, Any]) -> None:
    """Stop the whole refresh, before any change, when the DSS is not ready for the demo projects.

    Its tag categories must give the recap of the README, and no project it did not make may have a demo key. It
    reads them with a client of its own, before the admin fixture, which installs the plugin. It comes after the
    opt-in: pytest orders the autouse fixtures of a file by name, so it asks for the opt-in by name.
    """
    client = connect(config, "admin")
    try:
        check_tag_categories(client)
        for project_key in DEMO_KEYS:
            check_demo_key_is_free(client, project_key)
    except DemoProjectError as error:
        pytest.exit(str(error), returncode=pytest.ExitCode.TESTS_FAILED)


@pytest.fixture
def demo_projects(admin: Any, config: dict[str, Any], connection: str) -> Iterator[DemoProjects]:
    """Return the demo projects, made for the test. They are deleted at the end, also when the test fails."""
    try:
        yield create_demo_projects(admin, config["project_owner"], connection)
    finally:
        delete_demo_projects(admin)


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
def open_dss_page(config: dict[str, Any], ui_login: UiLogin, browser: Any) -> Iterator[Callable[[], Any]]:
    """Return a function that opens a page of Chromium, logged in to the DSS UI, when the test is ready for it.

    The page is in English, in the light theme, at scale 2. The pages are closed at the end of the test. The function
    raises DssUiError when DSS refuses the login.
    """
    contexts = []

    def open_page() -> Any:
        context = browser.new_context(
            base_url=config["url"],
            locale="en-US",
            color_scheme="light",
            device_scale_factor=SCALE,
            viewport=dss_ui.WINDOW_SIZE,
        )
        contexts.append(context)
        page = context.new_page()
        dss_ui.log_in(page, ui_login.login, ui_login.password)
        return page

    yield open_page
    for context in contexts:
        context.close()
