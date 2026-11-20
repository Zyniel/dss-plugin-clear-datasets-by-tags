"""The problems of a run, and the outcome they set.

A problem is a failure of the work, or of the summary dataset. This module turns each problem into
all that shows it: its banner, its log line, its part of the message of a failed run, and its entry
in the JSON recap. The macro only says what failed in its work, once: describe_failures(). The
runner adds the problems to the page of the macro, so recap/html.py shows them as it shows the rest.

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
from recap.page import TONE_CAUTION, TONE_DANGER, Banner, RecapPage
from recap.text import describe_dss_error

OUTCOME_SUCCESS = "SUCCESS"  # Nothing went wrong.
OUTCOME_WARNING = "WARNING"  # Something went wrong, and the run went on.
OUTCOME_FAILED = "FAILED"  # Something went wrong, and the form asked to fail the run.


class Problem(NamedTuple):
    """A failure of the work, or of the summary dataset."""

    message: str  # For the log, the JSON recap and the message of a failed run.
    fails_run: bool  # Its choice in the form ends the run in error.
    banner: Banner  # How the recap of a run that goes on shows it.


def set_work_problem(macro: MaintenanceMacro, recap: dict[str, Any]) -> None:
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
    """Add the summary dataset to the problems if it was not written, and update the outcome.

    Call it after set_work_problem(), once the summary dataset is written or has failed.
    """
    result = recap["recap_dataset_result"]
    if not (result and result["error"]):
        return
    error = describe_dss_error(result["error"])
    problem = Problem(
        f"Summary not written to dataset {result['name']}. {error}",
        recap["options"].get("on_recap_error") == ON_ERROR_FAIL,
        Banner(TONE_CAUTION, "Summary not written.", f"Dataset {result['name']}. {error}"),
    )
    set_problems(recap, [*recap["problems"], problem])


def set_problems(recap: dict[str, Any], problems: list[Problem]) -> None:
    """Set the problems of the run in the recap, and the outcome they give."""
    if any(problem.fails_run for problem in problems):
        outcome = OUTCOME_FAILED
    elif problems:
        outcome = OUTCOME_WARNING
    else:
        outcome = OUTCOME_SUCCESS
    recap.update(problems=problems, outcome=outcome)


def with_problems(page: RecapPage, recap: dict[str, Any]) -> RecapPage:
    """Return the page of the macro with the problems of the run.

    It gets the banner of each problem, and its JSON summary gets the outcome and the problems, as
    every recap has them: the RECAP_JSON line of the log and the hidden block of the HTML hold it.
    """
    problems = recap["problems"]
    return page._replace(
        banners=page.banners + [problem.banner for problem in problems],
        summary={**page.summary, "outcome": recap["outcome"], "problems": [problem.message for problem in problems]},
    )


def log_problems(recap: dict[str, Any], logger: logging.Logger) -> None:
    """Log each problem, as an ERROR when it fails the run, else as a WARNING, then the outcome.

    :param logger: the logger of the runner, so that these lines come from core.runner, like the rest of the run
    """
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
    return " ".join([*messages, details])
