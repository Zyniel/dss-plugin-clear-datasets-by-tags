"""A minimal macro, to test the shared code without any real macro.

It also shows the least a macro must provide. It marks each dataset of the project as done, or as
failed when its name is in config["fail"]. config["banners"] gives the banners of its page, and
config["notices"] its notices, each as (tone, title) pairs.
"""

from collections.abc import Callable
from typing import Any, Optional

from core.macro import MaintenanceMacro, RunBlockedError, WorkFailure
from core.options import read_recap_options, read_run_options
from core.project import list_project_datasets
from recap.page import (
    ALL_STATUSES,
    COLUMN_STATUS,
    ICON_CHECK,
    ICON_CROSS,
    TONE_DANGER,
    TONE_SUCCESS,
    Banner,
    Column,
    Metric,
    RecapPage,
    Status,
    Table,
)

SUMMARY_COLUMNS = ["run_id", "dataset", "status"]
STATUS_DONE = "DONE"
STATUS_FAILED = "FAILED"
STATUSES = [
    Status(STATUS_FAILED, "Failed", TONE_DANGER, ICON_CROSS),
    Status(STATUS_DONE, "Done", TONE_SUCCESS, ICON_CHECK),
]


class SampleMacro(MaintenanceMacro):
    """Marks each dataset of the project done, or failed when config["fail"] names it."""

    id = "sample-macro"
    label = "Sample Macro"
    summary_columns = SUMMARY_COLUMNS

    def run(
        self, project: Any, project_key: str, config: dict[str, Any], progress_callback: Callable[[int], None]
    ) -> dict[str, Any]:
        """Mark each dataset, and return the recap.

        :raises ValueError: if the "Summary" section of the form is not valid
        :raises RunBlockedError: when config["stop"] is set, as a blocker would
        """
        options = {**read_run_options(config), **read_recap_options(config, project_key)}
        if config.get("stop"):
            raise RunBlockedError("Nothing was done.")
        failing = config.get("fail") or []
        rows = [
            {"name": dataset["name"], "status": STATUS_FAILED if dataset["name"] in failing else STATUS_DONE}
            for dataset in list_project_datasets(project, project_key)
        ]
        progress_callback(100)
        return {
            "options": options,
            "banners": [Banner(tone, title) for tone, title in config.get("banners", [])],
            "notices": [Banner(tone, title) for tone, title in config.get("notices", [])],
            "blockers": [],
            "datasets": rows,
        }

    def describe_counts(self, recap: dict[str, Any]) -> str:
        """Return the number of datasets."""
        return f"{len(recap['datasets'])} datasets"

    def build_recap_rows(self, recap: dict[str, Any]) -> list[list[str]]:
        """Return one row per dataset: the run, the dataset and its status."""
        return [[recap["run_id"], row["name"], row["status"]] for row in recap["datasets"]]

    def build_recap_page(self, recap: dict[str, Any]) -> RecapPage:
        """Return a page with one figure and the table of the datasets."""
        columns = [Column("name", "Dataset", pinned=True), Column("status", "Status", COLUMN_STATUS)]
        table = Table("Datasets", columns, STATUSES, recap["datasets"], "No dataset.", "Search", "sample.csv")
        metrics = [Metric("Datasets", str(len(recap["datasets"])), status=ALL_STATUSES)]
        summary = {"run_id": recap["run_id"], "run_by": recap["run_by"], "datasets": recap["datasets"]}
        return RecapPage(recap["banners"], metrics, [], table, summary)

    def describe_failures(self, recap: dict[str, Any]) -> Optional[WorkFailure]:
        """Return the names of the failed datasets, or None."""
        failed = [row["name"] for row in recap["datasets"] if row["status"] == STATUS_FAILED]
        return WorkFailure(f"Failed: {', '.join(failed)}.", 'Click "Failed".') if failed else None


MACRO = SampleMacro()
