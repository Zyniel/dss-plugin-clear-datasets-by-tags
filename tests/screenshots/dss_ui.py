"""The DSS UI, as the screenshot tests drive it: log in, open a macro, fill its form, run it, take a screenshot.

Every detail of the DSS UI that the Dataiku docs do not give is in this module, read on DSS 13.4.4: the labels of the
login form, the link to the Macros page, the dialog of a macro (its place, its buttons, its list fields, its body that
scrolls past 500 pixels, its width of 900 pixels, which the screenshots keep), the time a run takes, the size of the
window. When a DSS upgrade breaks a screenshot test, fix it here. The steps find fields and buttons by their visible
English labels and their roles, never by CSS classes.

What the Dataiku docs (DSS 13) give:

- /login/ is a login and password form for local users, also when SSO is on:
  https://doc.dataiku.com/dss/13/security/sso.html
- The macros of a project are in its "Macros" menu: https://doc.dataiku.com/dss/13/plugins/reference/macros.html
  A macro runs by clicking its name on that page, then filling its form:
  https://doc.dataiku.com/dss/13/operations/disk-usage.html

Each function takes a Playwright page (`playwright.sync_api.Page`) or locator, whose base URL is the URL of the DSS.
"""

import math
from typing import Any, NamedTuple, Optional

LOGIN_PAGE = "/login/"

# The labels of the DSS UI, read on DSS 13.4.4.
USERNAME = "Username"
PASSWORD = "Password"
LOG_IN = "Log in"
MACROS = "Macros"
RESET_TO_DEFAULT = "Reset to default"
RUN_MACRO = "Run macro"
CLOSE = "Close"
# The placeholder of a field of type STRINGS: a value, then Enter, adds it to the list.
LIST_PLACEHOLDER = "Type a value and press enter to add it to the list."

# The window of the browser: wider than the dialogs of the macros, and taller than the longest one once unfolded.
WINDOW_SIZE = {"width": 1280, "height": 1800}

# Long enough for a slow DSS. A login that fails stays on the login page this long.
LOGIN_TIMEOUT_MS = 20_000
# Long enough for a macro to run on the demo projects.
RUN_TIMEOUT_MS = 120_000

# DSS caps the body of a dialog at 500 pixels, and scrolls the rest: a taller window does not help. This shows each
# part of the dialog that scrolls whole, the outermost ones only: the inner parts, such as a table, keep their scroll.
# DSS shows the recap of a run in the dialog of its form: the height rounded for the form goes first.
UNFOLD = """dialog => {
    dialog.style.minHeight = '';
    const unfolded = [];
    for (const part of dialog.querySelectorAll('*')) {
        const scrolls = ['auto', 'scroll'].includes(getComputedStyle(part).overflowY);
        if (scrolls && part.scrollHeight > part.clientHeight && !unfolded.some(outer => outer.contains(part))) {
            part.style.maxHeight = 'none';
            part.style.overflowY = 'visible';
            unfolded.push(part);
        }
    }
}"""
# Rounds the height of the dialog up to a whole pixel, with less than a pixel of its own white.
ROUND_HEIGHT = "dialog => { dialog.style.minHeight = Math.ceil(dialog.getBoundingClientRect().height) + 'px'; }"
# The table of a recap sets its height a moment after the recap shows: the height must stay the same this long.
STILL_MS = 300
STILL_TIMEOUT_MS = 10_000


class DssUiError(Exception):
    """The DSS UI did not answer as this module expects: a login that fails, or a DSS UI that changed."""


class UiLogin(NamedTuple):
    """The login and the password of the DSS UI, from the config file."""

    login: str
    password: str


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


def find_dialog(page: Any, label: str, button: str) -> Any:
    """Return the dialog of a macro. It has no role: it is the smallest part of the page with its title and a button.

    :param label: the name of the macro, as runnable.json gives it: the title of the dialog
    :param button: a button only this dialog has: "Run macro" on the form, "Close" on the recap
    """
    return (
        page.locator("*", has=page.get_by_role("button", name=button, exact=True))
        .filter(has=page.get_by_text(label, exact=True))
        .last
    )


def find_field(dialog: Any, label: str, role: str, name: Optional[str] = None) -> Any:
    """Return a field of a form, by the label of its row: the smallest part of the dialog with the label and a field.

    :param name: the accessible name of the field, when its row has several fields of this role
    """
    page = dialog.page
    row = dialog.locator("*", has=page.get_by_text(label, exact=True)).filter(has=page.get_by_role(role)).last
    return row.get_by_role(role, name=name)


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
    dialog = find_dialog(page, label, RUN_MACRO)
    reset = dialog.get_by_role("button", name=RESET_TO_DEFAULT, exact=True)
    reset.click()
    # Neither a focused nor a hovered button in the screenshot.
    reset.blur()
    page.mouse.move(0, 0)
    return dialog


def fill_form(dialog: Any, params: dict[str, dict[str, Any]], values: dict[str, Any]) -> None:
    """Fill the form of a macro, as a user does: check or uncheck a box, add values to a list. The rest stays.

    Only the parameters of type STRINGS and BOOLEAN: the forms of the README need no other.

    :param params: the parameters of the form, from runnable.json, by name: their labels and their types
    :param values: the values to give, by name of parameter
    :raises DssUiError: for a parameter of another type.
    """
    for name, value in values.items():
        param_type, label = params[name]["type"], params[name]["label"]
        if param_type == "STRINGS":
            field = find_field(dialog, label, "textbox", name=LIST_PLACEHOLDER)
            for item in value:
                field.fill(item)
                field.press("Enter")
        elif param_type == "BOOLEAN":
            field = find_field(dialog, label, "checkbox")
            field.set_checked(value)
        else:
            raise DssUiError(f'The screenshot tests do not fill "{label}", a field of type {param_type}.')
        field.blur()
    dialog.page.mouse.move(0, 0)


def run_from_dialog(dialog: Any, label: str) -> Any:
    """Run a macro from its dialog, wait for its recap, and return the dialog that shows it.

    :param label: the name of the macro, as runnable.json gives it
    :raises DssUiError: when the recap does not show in time.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    page = dialog.page
    dialog.get_by_role("button", name=RUN_MACRO, exact=True).click()
    recap_dialog = find_dialog(page, label, CLOSE)
    try:
        recap_dialog.get_by_role("button", name=CLOSE, exact=True).wait_for(timeout=RUN_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        raise DssUiError(
            f"The recap of the {label} macro did not show after {RUN_TIMEOUT_MS // 1000} seconds: see the log of the "
            "run in DSS, or raise RUN_TIMEOUT_MS in tests/screenshots/dss_ui.py."
        ) from None
    page.wait_for_load_state("networkidle")
    page.mouse.move(0, 0)
    return recap_dialog


def wait_until_still(page: Any, dialog: Any) -> None:
    """Wait until the height of a dialog stays the same for STILL_MS.

    :raises DssUiError: when its height still changes after STILL_TIMEOUT_MS.
    """
    height = None
    for _ in range(STILL_TIMEOUT_MS // STILL_MS):
        box = dialog.bounding_box()
        if box is not None and box["height"] == height:
            return
        height = None if box is None else box["height"]
        page.wait_for_timeout(STILL_MS)
    raise DssUiError(f"The height of the dialog still changes after {STILL_TIMEOUT_MS // 1000} seconds.")


def take_screenshot(page: Any, dialog: Any) -> bytes:
    """Return the screenshot of a dialog, whole, as a PNG: the dialog only, with no line of the page behind it.

    DSS centres the dialog in the window. When an edge falls on half a pixel, Chrome draws the dialog on the next
    pixel, and the screenshot would take a line of the page behind it: the window then grows by one pixel.

    :raises DssUiError: when the dialog does not show, is taller than the window, or does not sit on whole pixels.
    """
    dialog.evaluate(UNFOLD)
    wait_until_still(page, dialog)
    dialog.evaluate(ROUND_HEIGHT)
    box = dialog.bounding_box()
    if box is None:
        raise DssUiError("The dialog of the macro does not show.")
    if box["x"] % 1 or box["y"] % 1:
        window = page.viewport_size
        width = window["width"] + (1 if box["x"] % 1 else 0)
        height = window["height"] + (1 if box["y"] % 1 else 0)
        page.set_viewport_size({"width": width, "height": height})
        box = dialog.bounding_box()
    if any(box[side] % 1 for side in ("x", "y", "width", "height")):
        raise DssUiError(f"The dialog does not sit on whole pixels: {box}. See take_screenshot().")
    if box["y"] < 0 or box["y"] + box["height"] > page.viewport_size["height"]:
        raise DssUiError(
            f"The dialog, {box['height']:.0f} pixels high, is taller than the window: raise WINDOW_SIZE in "
            "tests/screenshots/dss_ui.py."
        )
    clip = {side: math.floor(box[side]) for side in ("x", "y", "width", "height")}
    screenshot: bytes = page.screenshot(clip=clip, animations="disabled")
    return screenshot
