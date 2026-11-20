"""The refresh of the README screenshots, on the demo projects of the test DSS: see docs/screenshots.md."""

from typing import Any, Callable

from integration.dss import run_macro
from screenshots import dss_ui
from screenshots.demo_projects import SALES, DemoProjects, ReadmeMacro, describe_differences, list_readme_macros
from screenshots.images import build_readme_image, find_page_edges, write_readme_images
from support.pages import read_summary


def describe_api_differences(demo_projects: DemoProjects, macros: list[ReadmeMacro]) -> list[str]:
    """Run each macro on SALES through the API, and describe the results that differ from what the README states."""
    differences = []
    for macro in macros:
        recap = run_macro(demo_projects.sales, macro.runnable_id, macro.form)
        differences += describe_differences(macro.label, macro.expected, macro.read_results(recap))
    return differences


# open_dss_page comes first: a config file with no UI login stops the test before any change on the DSS.
def test_a_refresh_takes_the_readme_screenshots_on_the_demo_projects(
    open_dss_page: Callable[[], Any], ui_login: dss_ui.UiLogin, demo_projects: DemoProjects
) -> None:
    macros = list_readme_macros()
    differences = describe_api_differences(demo_projects, macros)
    # Before any browser step: when a result differs from the README, no image changes.
    assert not differences, "The recaps differ from what the README states:\n" + "\n".join(differences)

    page = open_dss_page()
    images = {}
    for macro in macros:
        dialog = dss_ui.open_macro(page, SALES, macro.label)
        dss_ui.fill_form(dialog, macro.params, macro.form)
        images[macro.macro_id, "form"] = build_readme_image(dss_ui.take_screenshot(page, dialog))
        recap_dialog = dss_ui.run_from_dialog(dialog, macro.label)
        images[macro.macro_id, "recap"] = build_readme_image(dss_ui.take_screenshot(page, recap_dialog))
        # The recap shown is the one of this run in the UI: its results, and its user.
        ui_recap = read_summary(recap_dialog.inner_html())
        differences += describe_differences(macro.label, macro.expected, macro.read_results(ui_recap))
        if ui_recap["run_by"] != ui_login.login:
            differences.append(f"The {macro.label} macro ran in the UI as {ui_recap['run_by']}, not {ui_login.login}.")

    assert not differences, "The recaps in the UI differ from what the README states:\n" + "\n".join(differences)
    page_edges = {
        f"{macro_id}/{name}": edges for (macro_id, name), png in images.items() if (edges := find_page_edges(png))
    }
    assert not page_edges, f"Lines of the page behind the dialog, inside the frame: {page_edges}"
    # All the images, or none: a failure above leaves the old ones as they were.
    write_readme_images(images)
