"""The problems of a run, and the outcome they set.

A problem is a failure of the work, or of the summary dataset. This module turns each problem into
all that shows it: its banner, its log line, its part of the message of a failed run, and its entry
in the JSON recap. The macro only says what failed in its work, once: describe_failures().

The outcome of a run is:

- SUCCESS: no problem;
- WARNING: problems, and the run goes on, as the form asked. DSS shows the run as a success: it has
  no warning for a macro. So the recap shows each problem in a banner, and the log in a WARNING line;
- FAILED: a problem whose choice in the form ends the run in error. The run raises: it has no page.
"""

import logging
from typing import Any, NamedTuple

from core.macro import MaintenanceMacro
from core.options import FAILING_ON_ERROR, ON_ERROR_FAIL
from recap.html import dss_said
from recap.page import TONE_CAUTION, TONE_DANGER, Banner

OUTCOME_SUCCESS = "SUCCESS"  # Nothing went wrong.
OUTCOME_WARNING = "WARNING"  # Something went wrong, and the run went on.
OUTCOME_FAILED = "FAILED"  # Something went wrong, and the form asked to fail the run.


class Problem(NamedTuple):
    """A failure of the work, or of the summary dataset."""

    message: str  # For the log, the JSON recap and the message of a failed run.
    fails_run: bool  # Its choice in the form ends the run in error.
    banner: Banner  # How the recap of a run that goes on shows it.


def add_work_problem(macro: MaintenanceMacro, recap: dict[str, Any]) -> None:
    """Set the problems of the run to the failure of its work, if any, and set the outcome.

    Call it once, right after the work: it asks the macro what failed.
    """
    problems = []
    failure = macro.describe_failures(recap)
    if failure:
        # Only the macros that change data have "If an error occurs", in their "Run" section.
        fails_run = recap["options"].get("on_error") in FAILING_ON_ERROR
        problems.append(Problem(failure.message, fails_run, Banner(TONE_DANGER, failure.message, failure.hint)))
    set_problems(recap, problems)


def add_summary_dataset_problem(recap: dict[str, Any]) -> None:
    """Add the summary dataset to the problems if it was not written, and update the outcome."""
    result = recap["recap_dataset_result"]
    if not (result and result["error"]):
        return
    error = dss_said(result["error"])
    problem = Problem(
        f"Summary not written to dataset {result['name']}. {error}",
        recap["options"].get("on_recap_error") == ON_ERROR_FAIL,
        Banner(TONE_CAUTION, "Summary not written.", f"Dataset {result['name']}. {error}"),
    )
    set_problems(recap, recap["problems"] + [problem])


def set_problems(recap: dict[str, Any], problems: list[Problem]) -> None:
    """Set the problems of the run in the recap, and the outcome they give."""
    if any(problem.fails_run for problem in problems):
        outcome = OUTCOME_FAILED
    elif problems:
        outcome = OUTCOME_WARNING
    else:
        outcome = OUTCOME_SUCCESS
    recap.update(problems=problems, outcome=outcome)


def log_problems(recap: dict[str, Any], logger: logging.Logger) -> None:
    """Log each problem, as an ERROR when it fails the run, else as a WARNING, then the outcome."""
    for problem in recap["problems"]:
        log = logger.error if problem.fails_run else logger.warning
        log("Problem: %s", problem.message)
    logger.info("Outcome: %s", recap["outcome"])


def build_failure_message(recap: dict[str, Any]) -> str:
    """Return the message of a failed run: every problem, the work first, then where the details are.

    DSS shows only this message, so it also gives the problems that do not fail the run.
    """
    messages = [problem.message for problem in recap["problems"]]
    result = recap["recap_dataset_result"]
    written = result and not result["error"]
    details = f"Details in the summary dataset {result['name']}." if written else "Details in the run log."
    return " ".join(messages + [details])
