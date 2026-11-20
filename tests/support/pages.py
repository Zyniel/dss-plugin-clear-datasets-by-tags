"""Read an HTML recap as its reader or the API does: its figures and its hidden JSON blocks."""

import json
import re
from typing import Any


def metric_value(html: str, label: str) -> str:
    """Return the value shown above the label of a figure."""
    before_label = html[: html.index(f'<span class="dtp-metric-label">{label}<')]
    value_start = before_label.rindex('">') + 2
    return before_label[value_start:].replace("</span>", "")


def read_json_block(html: str, attribute: str) -> Any:
    """Return the data of the <script type="application/json"> block with this attribute. Fails the test if none."""
    block = re.search(rf'<script type="application/json" {re.escape(attribute)}>(.*?)</script>', html, re.DOTALL)
    assert block, f"The recap has no JSON block {attribute}."
    return json.loads(block.group(1))


def read_summary(html: str) -> dict[str, Any]:
    """Return the JSON recap of the hidden block of the recap, as the API reads it."""
    summary: dict[str, Any] = read_json_block(html, 'id="dtp-recap-data"')
    return summary


def read_table_rows(html: str) -> list[dict[str, Any]]:
    """Return the rows of the hidden block of the table, as the grid script reads them."""
    rows: list[dict[str, Any]] = read_json_block(html, 'class="dtp-table-data"')
    return rows
