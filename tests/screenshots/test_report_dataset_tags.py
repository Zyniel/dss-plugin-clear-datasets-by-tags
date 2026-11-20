"""The README screenshots of the Report Dataset Tags macro, taken on the test DSS: see docs/screenshots.md."""

from typing import Any

from screenshots import dss_ui
from screenshots.images import FRAME_WIDTH, SCALE, build_readme_image, read_size, write_readme_image
from support.forms import read_form

MACRO_ID = "report-dataset-tags"


# dss_page comes first: a config file with no UI login stops the test before any change on the DSS.
def test_the_readme_shows_the_form_of_the_report_dataset_tags_macro_with_its_default_values(
    dss_page: Any, scratch_project: Any
) -> None:
    dialog = dss_ui.open_macro(dss_page, scratch_project.project_key, read_form(MACRO_ID)["meta"]["label"])

    image = build_readme_image(dss_ui.take_screenshot(dss_page, dialog))

    # Only the dialog, at scale 2, in its frame: no line of the page behind it.
    box = dialog.bounding_box()
    assert read_size(image) == (SCALE * box["width"] + 2 * FRAME_WIDTH, SCALE * box["height"] + 2 * FRAME_WIDTH)
    write_readme_image(MACRO_ID, "form", image)
