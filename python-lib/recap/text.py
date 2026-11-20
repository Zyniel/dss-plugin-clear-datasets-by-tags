"""Text for the messages of a run: counts, durations, dates and errors.

None of it is HTML: recap/html.py escapes it where it shows it. A format_* function turns one value
into a short text, and a describe_* function writes a sentence for the reader.
"""

from typing import Any

# The length of an error of DSS in a message. The log has the whole error.
DSS_ERROR_SHOWN = 200


def format_count(count: int, noun: str) -> str:
    """Return "1 dataset" or "2 datasets": the count with its noun, in the singular for one."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def format_duration(seconds: float) -> str:
    """Return a duration for reading, such as "0.42 s" or "3.5 min"."""
    if seconds < 60:
        return f"{seconds:.2f} s"
    return f"{seconds / 60:.1f} min"


def format_started_at(started_at: str) -> str:
    """Return "2026-11-02 19:10:00 UTC" for "2026-11-02T19:10:00Z"."""
    return started_at.replace("T", " ").replace("Z", " UTC")


def format_yes_no(value: bool) -> str:
    """Return "yes" or "no", for the options shown in a recap."""
    return "yes" if value else "no"


def format_error(error: Exception) -> str:
    """Return an exception as its type and its message, such as "OSError: disk full"."""
    return f"{type(error).__name__}: {error}"


def describe_dss_error(error: Any) -> str:
    """Return an error of DSS for the end of a message, such as "DSS said: Disk full.", cut when it is long."""
    message = " ".join(str(error).split()) or type(error).__name__
    if len(message) > DSS_ERROR_SHOWN:
        return f"DSS said: {message[:DSS_ERROR_SHOWN]}..."
    return f"DSS said: {message.rstrip('.')}."
