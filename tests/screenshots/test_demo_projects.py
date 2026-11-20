"""The demo projects of the README screenshots on the test DSS, and the results the README states for them.

The guard is tested on scratch projects of the integration tests: they stand for a project with a demo key.
See docs/screenshots.md.
"""

from typing import Any

import pytest

from integration.dss import CLEAR, REPORT, run_macro
from screenshots.demo_projects import (
    CLEAR_FORM,
    EXPECTED_CLEAR,
    EXPECTED_REPORT,
    REPORT_FORM,
    DemoProjectError,
    DemoProjects,
    check_demo_key_is_free,
    delete_demo_project,
    describe_differences,
    mark_demo_project,
    read_clear_results,
    read_report_results,
)
from support.forms import read_form


def test_the_demo_projects_give_the_results_the_readme_states(demo_projects: DemoProjects) -> None:
    clear_recap = run_macro(demo_projects.sales, CLEAR, CLEAR_FORM)
    report_recap = run_macro(demo_projects.sales, REPORT, REPORT_FORM)

    clear_label = read_form("clear-datasets-by-tags")["meta"]["label"]
    report_label = read_form("report-dataset-tags")["meta"]["label"]
    differences = describe_differences(clear_label, EXPECTED_CLEAR, read_clear_results(clear_recap))
    differences += describe_differences(report_label, EXPECTED_REPORT, read_report_results(report_recap))
    assert not differences, "The recaps differ from what the README states:\n" + "\n".join(differences)


def test_a_project_with_a_demo_key_and_no_mark_stops_the_refresh(admin: Any, scratch_project: Any) -> None:
    project_key = scratch_project.project_key

    with pytest.raises(DemoProjectError, match=f"A project {project_key} exists, and the refresh did not make it"):
        check_demo_key_is_free(admin, project_key)

    assert project_key in admin.list_project_keys()


def test_the_refresh_never_deletes_a_project_with_a_demo_key_and_no_mark(admin: Any, scratch_project: Any) -> None:
    project_key = scratch_project.project_key

    with pytest.raises(DemoProjectError, match=f"The project {project_key} has no mark of a demo project"):
        delete_demo_project(admin, project_key)

    assert project_key in admin.list_project_keys()


def test_a_demo_project_left_by_a_refresh_that_crashed_is_deleted(admin: Any, scratch_project: Any) -> None:
    project_key = scratch_project.project_key
    mark_demo_project(scratch_project)

    check_demo_key_is_free(admin, project_key)
    delete_demo_project(admin, project_key)

    assert project_key not in admin.list_project_keys()
