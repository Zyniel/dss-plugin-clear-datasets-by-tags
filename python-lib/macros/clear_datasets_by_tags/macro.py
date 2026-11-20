"""The MaintenanceMacro of "Clear Datasets by Tags": what the shared runner calls."""

from collections.abc import Callable
from typing import Any, Optional

from core.macro import MaintenanceMacro, WorkFailure
from macros.clear_datasets_by_tags.clearing import run_clearing
from macros.clear_datasets_by_tags.recap import (
    SUMMARY_COLUMNS,
    build_recap_page,
    build_recap_rows,
    describe_counts,
    describe_failures,
)
from recap.page import RecapPage


class ClearDatasetsByTagsMacro(MaintenanceMacro):
    """Clears the data of the datasets with the included tags, or of all datasets, except the excluded ones.

    Each method calls the function of the same name in clearing.py or recap.py.
    """

    id = "clear-datasets-by-tags"
    label = "Clear Datasets by Tags"
    summary_columns = SUMMARY_COLUMNS

    def run(
        self, project: Any, project_key: str, config: dict[str, Any], progress_callback: Callable[[int], None]
    ) -> dict[str, Any]:
        return run_clearing(project, project_key, config, progress_callback)

    def describe_counts(self, recap: dict[str, Any]) -> str:
        return describe_counts(recap)

    def build_recap_rows(self, recap: dict[str, Any]) -> list[list[str]]:
        return build_recap_rows(recap)

    def build_recap_page(self, recap: dict[str, Any]) -> RecapPage:
        return build_recap_page(recap)

    def describe_failures(self, recap: dict[str, Any]) -> Optional[WorkFailure]:
        return describe_failures(recap)


MACRO = ClearDatasetsByTagsMacro()
