"""Tests of the text of the messages: counts, durations, dates and errors."""

from recap.text import (
    describe_dss_error,
    format_count,
    format_duration,
    format_error,
    format_started_at,
    format_yes_no,
)


def test_format_count() -> None:
    assert format_count(0, "row") == "0 rows"
    assert format_count(1, "row") == "1 row"
    assert format_count(2, "dataset") == "2 datasets"


def test_format_duration() -> None:
    assert format_duration(0.421) == "0.42 s"
    assert format_duration(90) == "1.5 min"


def test_format_started_at() -> None:
    assert format_started_at("2026-11-02T19:10:00Z") == "2026-11-02 19:10:00 UTC"


def test_format_yes_no() -> None:
    assert (format_yes_no(True), format_yes_no(False)) == ("yes", "no")


def test_format_error_gives_its_type_then_its_message() -> None:
    assert format_error(OSError("disk full")) == "OSError: disk full"
    assert format_error(TimeoutError()) == "TimeoutError: "


def test_describe_dss_error_ends_with_one_period_and_cuts_a_long_error() -> None:
    assert describe_dss_error("disk full") == "DSS said: disk full."
    assert describe_dss_error("disk full.") == "DSS said: disk full."
    assert describe_dss_error(" line one\n  line two ") == "DSS said: line one line two."
    assert describe_dss_error(TimeoutError()) == "DSS said: TimeoutError."
    assert describe_dss_error("x" * 500) == f"DSS said: {'x' * 200}..."
