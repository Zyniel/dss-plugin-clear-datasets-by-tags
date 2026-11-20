"""The guard of the demo projects of the README screenshots, on the test DSS: see docs/screenshots.md.

It is tested on scratch projects of the integration tests: they stand for a project with a demo key. The refresh
test creates the demo projects and checks their results: see test_readme_screenshots.py.
"""

from typing import Any

import pytest

from screenshots.demo_projects import DemoProjectError, check_demo_key_is_free, delete_demo_project, mark_demo_project


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
