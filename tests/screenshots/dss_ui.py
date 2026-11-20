"""The DSS UI, as the screenshot tests drive it: log in, open a macro of a project, take a screenshot of its dialog.

Every detail of the DSS UI that the Dataiku docs do not give is in this module, read on DSS 13.4.4: the labels of the
login form, the link to the Macros page, the buttons and the place of the dialog of a macro, the size of the window
that shows it whole. When a DSS upgrade breaks a screenshot test, fix it here. The steps find fields and buttons by
their visible English labels and their roles, never by CSS classes.

What the Dataiku docs (DSS 13) give:

- /login/ is a login and password form for local users, also when SSO is on:
  https://doc.dataiku.com/dss/13/security/sso.html
- The macros of a project are in its "Macros" menu: https://doc.dataiku.com/dss/13/plugins/reference/macros.html
  A macro runs by clicking its name on that page, then filling its form:
  https://doc.dataiku.com/dss/13/operations/disk-usage.html

Each function takes a Playwright page (`playwright.sync_api.Page`) or locator, whose base URL is the URL of the DSS.
"""

from typing import Any

LOGIN_PAGE = "/login/"

# The labels of the DSS UI, read on DSS 13.4.4.
USERNAME = "Username"
PASSWORD = "Password"
LOG_IN = "Log in"
MACROS = "Macros"
RESET_TO_DEFAULT = "Reset to default"
RUN_MACRO = "Run macro"

# The window of the browser: wider and taller than the dialogs of the macros, so that DSS shows each one whole,
# without scrolling.
WINDOW_SIZE = {"width": 1280, "height": 1800}

# Long enough for a slow DSS. A login that fails stays on the login page this long.
LOGIN_TIMEOUT_MS = 20_000


class DssUiError(Exception):
    """The DSS UI did not answer as this module expects: a login that fails, or a DSS UI that changed."""


def log_in(page: Any, login: str, password: str) -> None:
    """Log in to the DSS UI through the login form, as a user does.

    API keys cannot open a session in the DSS UI: only a login and a password can.

    :raises DssUiError: when DSS refuses the login or the password.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    page.goto(LOGIN_PAGE)
    page.get_by_role("textbox", name=USERNAME).fill(login)
    page.get_by_role("textbox", name=PASSWORD).fill(password)
    page.get_by_role("button", name=LOG_IN).click()
    try:
        page.wait_for_url(lambda url: LOGIN_PAGE not in url, timeout=LOGIN_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        raise DssUiError(
            f'DSS refused the UI login "{login}". Check "ui_login" and "ui_password" in the config file.'
        ) from None


def open_macro(page: Any, project_key: str, label: str) -> Any:
    """Open the dialog of a macro of a project, with the default values of its form, and return the dialog.

    :param label: the name of the macro, as runnable.json gives it
    :raises DssUiError: when the page of the project has no link to its Macros page.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    page.goto(f"/projects/{project_key}/")
    # The "Macros" link is in a menu that opens on hover, from an icon with no label: read the link, do not click it.
    try:
        macros_page = page.get_by_role("link", name=MACROS, exact=True, include_hidden=True).get_attribute("href")
    except PlaywrightTimeoutError:
        macros_page = None
    if not macros_page:
        raise DssUiError(f'The page of the project has no "{MACROS}" link: see tests/screenshots/dss_ui.py.')
    page.goto(macros_page)
    page.get_by_text(label, exact=True).click()
    # The dialog has no role: it is the smallest part of the page that holds its title and its "Run macro" button.
    dialog = (
        page.locator("*", has=page.get_by_role("button", name=RUN_MACRO, exact=True))
        .filter(has=page.get_by_text(label, exact=True))
        .last
    )
    reset = dialog.get_by_role("button", name=RESET_TO_DEFAULT, exact=True)
    reset.click()
    # Neither a focused nor a hovered button in the screenshot.
    reset.blur()
    page.mouse.move(0, 0)
    return dialog


def take_screenshot(page: Any, dialog: Any) -> bytes:
    """Return the screenshot of a dialog, as a PNG: the dialog only, with no line of the page behind it.

    DSS centres the dialog in the window. When its edge falls on half a pixel, the screenshot takes a line of the page
    behind it: the window then grows by one pixel, and the dialog moves by half a pixel.

    :raises DssUiError: when the dialog does not show, or is taller than the window.
    """
    box = dialog.bounding_box()
    if box is None:
        raise DssUiError("The dialog of the macro does not show.")
    window = page.viewport_size
    if box["x"] % 1 or box["y"] % 1:
        width = window["width"] + (1 if box["x"] % 1 else 0)
        height = window["height"] + (1 if box["y"] % 1 else 0)
        page.set_viewport_size({"width": width, "height": height})
        window = page.viewport_size
        box = dialog.bounding_box()
    if box["y"] < 0 or box["y"] + box["height"] > window["height"]:
        raise DssUiError(
            f"The dialog, {box['height']:.0f} pixels high, is taller than the window: raise WINDOW_SIZE in "
            "tests/screenshots/dss_ui.py."
        )
    screenshot: bytes = dialog.screenshot(animations="disabled")
    return screenshot
