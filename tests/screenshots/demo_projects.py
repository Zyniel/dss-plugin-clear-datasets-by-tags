"""The demo projects of the README screenshots, SALES and FINANCE, and the results the README states for them.

A refresh builds them on the test DSS, runs both macros on SALES through the API, checks the results below, and
deletes the projects at the end. The datasets and their tags are those of the screenshots taken by hand on DSS 13.4.4.
When a change of the plugin changes a result on purpose, change the expected results and the README captions
together: see docs/screenshots.md.

A refresh never touches a project it did not make: it marks each project it creates with a project variable, and
checks the mark before it deletes one. Each function takes handles of the DSS API client (`dataikuapi`), as the
helpers of the integration tests do.
"""

from typing import Any, NamedTuple, Union

from integration.dss import (
    add_built_dataset,
    add_empty_dataset,
    add_partitioned_dataset,
    add_uploaded_dataset,
    delete_whole_project,
    set_recipe_tags,
    set_tags,
    share_dataset,
)

SALES = "SALES"
FINANCE = "FINANCE"
# FINANCE uses a dataset of SALES: it is deleted first.
DEMO_KEYS = (FINANCE, SALES)

# How a dataset of SALES is made.
UPLOADED = "UPLOADED"  # An uploaded dataset with 3 rows: DSS does not manage its data.
BUILT = "BUILT"  # A managed dataset with 3 rows, that a sync recipe builds from its source.
NO_RECIPE = "NO_RECIPE"  # A managed dataset with no data, that no recipe builds.
PARTITIONED = "PARTITIONED"  # A managed dataset with no data and no recipe, partitioned by day and country.


class DemoDataset(NamedTuple):
    """A dataset of SALES: its name, its tags, how it is made, and the input of its recipe."""

    name: str
    tags: list[str]
    kind: str
    source: str = ""


# In the order of the build: the input of a recipe comes before its output.
SALES_DATASETS = (
    DemoDataset("customers_upload", [], UPLOADED),  # The untagged dataset.
    DemoDataset("orders_upload", ["Stage:Raw"], UPLOADED),  # Not selected.
    DemoDataset("crm_extract", ["temporary", "Stage:Raw"], UPLOADED),  # Skipped: external.
    DemoDataset("raw_customers", ["temporary", "Stage:Raw"], BUILT, "customers_upload"),  # To clear.
    DemoDataset("raw_orders", ["temporary", "Stage:Raw"], BUILT, "orders_upload"),  # To clear.
    DemoDataset("orders_prepared", ["temporary", "Stage:Prepared"], BUILT, "raw_orders"),  # To clear.
    # Excluded, and an unknown tag: Stage:Ouput, a typo of Stage:Output.
    DemoDataset("orders_by_month", ["temporary", "keep", "Stage:Ouput"], BUILT, "orders_prepared"),
    DemoDataset("sales_report", ["Stage:Output"], BUILT, "orders_prepared"),  # Not selected.
    # To clear, and shared with FINANCE: a risk. An unknown tag: Owner:Finance, as DSS has no tag category Owner.
    DemoDataset("country_lookup", ["temporary", "Owner:Finance"], BUILT, "customers_upload"),
    DemoDataset("manual_targets", ["temporary"], NO_RECIPE),  # Skipped: with no recipe.
    DemoDataset("web_logs", ["temporary"], PARTITIONED),  # Skipped: partitioned.
)
SHARED_DATASET = "country_lookup"
# On the recipe of sales_report: in the project tag list of SALES, on no dataset.
UNUSED_TAG = "archive"
UNUSED_TAG_DATASET = "sales_report"
# The dataset of FINANCE that its recipe builds from the shared dataset of SALES.
FINANCE_DATASET = "countries"

# The tag categories of DSS that the recap of the Report Dataset Tags macro needs. DSS has them for every project.
STAGE_CATEGORY = "Stage"
STAGE_TAGS = ("Raw", "Prepared", "Output")
UNKNOWN_CATEGORY = "Owner"  # Owner:Finance is an unknown tag.
TAG_CATEGORIES_PAGE = "Administration > Settings > Global tag categories"


class ClearResults(NamedTuple):
    """The results of a run of the Clear Datasets by Tags macro that the README states."""

    scanned: int
    selected: int
    to_clear: list[str]
    shared_to_clear: list[str]
    skipped: dict[str, str]  # The skip code of each skipped dataset.
    excluded: list[str]


class ReportResults(NamedTuple):
    """The results of a run of the Report Dataset Tags macro that the README states."""

    datasets: int
    tagged: int
    untagged: list[str]
    tags: int
    used: int
    unknown: list[str]
    unused: list[str]


# The forms of the runs, as the README describes them.
CLEAR_FORM = {"included_tags": ["temporary"], "excluded_tags": ["keep"], "simulate": True}
REPORT_FORM: dict[str, Any] = {}  # The default values.

# The results the README states. Change them together with the README captions.
EXPECTED_CLEAR = ClearResults(
    scanned=11,
    selected=8,
    to_clear=["country_lookup", "orders_prepared", "raw_customers", "raw_orders"],
    shared_to_clear=["country_lookup"],
    skipped={"crm_extract": "EXTERNAL", "manual_targets": "WITHOUT_RECIPE", "web_logs": "PARTITIONED"},
    excluded=["orders_by_month"],
)
EXPECTED_REPORT = ReportResults(
    datasets=11,
    tagged=10,
    untagged=["customers_upload"],
    tags=8,
    used=5,
    unknown=["Owner:Finance", "Stage:Ouput"],
    unused=["archive"],
)

# The mark of a demo project: a project variable, which no macro reads.
MARK = "readme_demo_project"
MARK_VALUE = "Made by the screenshot tests of the plugin, which delete it at the end of each refresh."


class DemoProjectError(Exception):
    """The DSS is not ready for the demo projects, or a demo project could not be deleted."""


class DemoProjects(NamedTuple):
    """The handles of the demo projects."""

    sales: Any
    finance: Any


def read_tag_categories(client: Any) -> dict[str, set[str]]:
    """Return the global tag categories of DSS, with their tags.

    The same instance-wide setting, read the same way, as read_tag_categories() of the Report Dataset Tags macro.
    """
    settings = client.get_general_settings().get_raw()
    return {
        str(category.get("name") or ""): {str(tag.get("name") or "") for tag in category.get("globalTags") or []}
        for category in settings.get("globalTagsCategories") or []
    }


def format_quoted(names: list[str]) -> str:
    """Return '"A", "B" and "C"': names for a message, each between double quotes."""
    quoted = [f'"{name}"' for name in names]
    return " and ".join([", ".join(quoted[:-1]), quoted[-1]]) if len(quoted) > 1 else "".join(quoted)


def describe_tag_category_changes(categories: dict[str, set[str]]) -> list[str]:
    """Return the changes to the tag categories of DSS that the README needs, or none."""
    changes = []
    if STAGE_CATEGORY not in categories:
        changes.append(f'Create the tag category "{STAGE_CATEGORY}", with the tags {format_quoted(list(STAGE_TAGS))}.')
    else:
        missing = [tag for tag in STAGE_TAGS if tag not in categories[STAGE_CATEGORY]]
        if missing:
            changes.append(f'Add the tags {format_quoted(missing)} to the tag category "{STAGE_CATEGORY}".')
    if UNKNOWN_CATEGORY in categories:
        changes.append(
            f'Rename or delete the tag category "{UNKNOWN_CATEGORY}": the README shows "Owner:Finance" as unknown.'
        )
    return changes


def check_tag_categories(client: Any) -> None:
    """Check that the tag categories of DSS give the recap of the README. A refresh never changes them.

    :raises DemoProjectError: with the changes a DSS administrator must make.
    """
    changes = describe_tag_category_changes(read_tag_categories(client))
    if changes:
        raise DemoProjectError(
            f"The tag categories of DSS do not give the recap of the README. A DSS administrator must change them, "
            f"in {TAG_CATEGORIES_PAGE}, then run the refresh again:\n- " + "\n- ".join(changes)
        )


def mark_demo_project(project: Any) -> None:
    """Mark a project as a demo project, made by a refresh: a refresh may delete it."""
    variables = project.get_variables()
    variables.setdefault("standard", {})[MARK] = MARK_VALUE
    project.set_variables(variables)


def is_marked(client: Any, project_key: str) -> bool:
    """Return whether a project has the mark of a demo project: a refresh made it."""
    variables = client.get_project(project_key).get_variables()
    return bool((variables.get("standard") or {}).get(MARK) == MARK_VALUE)


def check_demo_key_is_free(client: Any, project_key: str) -> None:
    """Check that no project has this key, or only a demo project left by a refresh that crashed.

    :raises DemoProjectError: when a project has this key and no mark: a refresh never touches it.
    """
    if project_key in client.list_project_keys() and not is_marked(client, project_key):
        raise DemoProjectError(
            f"A project {project_key} exists, and the refresh did not make it: it never touches it. "
            "Rename or delete this project, then run the refresh again."
        )


def delete_demo_project(client: Any, project_key: str) -> None:
    """Delete a demo project, with its data, when there is one: a project a refresh made, never only its key.

    :raises DemoProjectError: when the project has this key and no mark.
    :raises RuntimeError: when the project is still there after the delete.
    """
    if project_key not in client.list_project_keys():
        return
    if not is_marked(client, project_key):
        raise DemoProjectError(f"The project {project_key} has no mark of a demo project: it is not deleted.")
    delete_whole_project(client, project_key)


def try_to_delete_demo_project(client: Any, project_key: str) -> str:
    """Delete a demo project when there is one, and return why the delete failed, or ""."""
    try:
        delete_demo_project(client, project_key)
    except (DemoProjectError, RuntimeError) as error:
        return str(error)
    return ""


def delete_demo_projects(client: Any) -> None:
    """Delete the demo projects there are, FINANCE first: it uses a dataset of SALES. Each one, even if one fails.

    :raises DemoProjectError: when a demo project could not be deleted, with the reason of each one.
    """
    failures = [failure for project_key in DEMO_KEYS if (failure := try_to_delete_demo_project(client, project_key))]
    if failures:
        raise DemoProjectError("Delete the demo projects by hand: " + " ".join(failures))


def create_marked_project(client: Any, project_key: str, owner: str) -> Any:
    """Create an empty demo project, and mark it at once: a refresh that crashes leaves a project it may delete.

    :param owner: the login of the owner of the project
    """
    project = client.create_project(project_key, project_key.capitalize(), owner)
    try:
        mark_demo_project(project)
    except Exception:
        # Unmarked, the project would stop every refresh: delete it while it is surely the one just made.
        delete_whole_project(client, project_key)
        raise
    return project


def add_sales_dataset(sales: Any, dataset: DemoDataset, connection: str) -> None:
    """Add a dataset of SALES to the project, as its kind says.

    :raises ValueError: for a kind of dataset that is not one of UPLOADED, BUILT, NO_RECIPE and PARTITIONED.
    """
    if dataset.kind == UPLOADED:
        add_uploaded_dataset(sales, dataset.name, dataset.tags)
    elif dataset.kind == BUILT:
        recipe = add_built_dataset(sales, dataset.name, dataset.tags, connection, source=dataset.source)
        if dataset.name == UNUSED_TAG_DATASET:
            set_recipe_tags(recipe, [UNUSED_TAG])
    elif dataset.kind == NO_RECIPE:
        set_tags(add_empty_dataset(sales, dataset.name, connection), dataset.tags)
    elif dataset.kind == PARTITIONED:
        add_partitioned_dataset(sales, dataset.name, dataset.tags, connection)
    else:
        raise ValueError(f"The dataset {dataset.name} has an unknown kind: {dataset.kind}.")


def create_demo_projects(client: Any, owner: str, connection: str) -> DemoProjects:
    """Create the demo projects, in place of those a refresh that crashed left, and fill them.

    :param owner: the login of the owner of the projects
    :raises DemoProjectError: when a demo project left by a refresh could not be deleted.
    """
    delete_demo_projects(client)
    finance = create_marked_project(client, FINANCE, owner)
    sales = create_marked_project(client, SALES, owner)
    for dataset in SALES_DATASETS:
        add_sales_dataset(sales, dataset, connection)
    share_dataset(sales, SHARED_DATASET, FINANCE)
    add_built_dataset(finance, FINANCE_DATASET, [], connection, source=SHARED_DATASET, source_project_key=SALES)
    return DemoProjects(sales, finance)


def read_clear_results(recap: dict[str, Any]) -> ClearResults:
    """Return the results of a run of the Clear Datasets by Tags macro, from its JSON recap."""
    rows = recap["datasets"]
    to_clear = [row for row in rows if row["status"] == "WOULD_BE_CLEARED"]
    return ClearResults(
        scanned=recap["counts"]["scanned"],
        selected=recap["counts"]["selected"],
        to_clear=sorted(row["name"] for row in to_clear),
        shared_to_clear=sorted(row["name"] for row in to_clear if row["is_shared"]),
        skipped={row["name"]: row["skip_code"] for row in rows if row["status"] == "SKIPPED"},
        excluded=sorted(row["name"] for row in rows if row["status"] == "EXCLUDED"),
    )


def read_report_results(recap: dict[str, Any]) -> ReportResults:
    """Return the results of a run of the Report Dataset Tags macro, from its JSON recap."""
    counts = recap["counts"]
    return ReportResults(
        datasets=counts["datasets"],
        tagged=counts["tagged"],
        untagged=sorted(recap["untagged_datasets"]),
        tags=counts["tags"],
        used=counts["used"],
        unknown=sorted(row["tag"] for row in recap["tags"] if row["status"] == "UNKNOWN"),
        unused=sorted(row["tag"] for row in recap["tags"] if row["status"] == "UNUSED"),
    )


def describe_differences(
    macro_label: str, expected: Union[ClearResults, ReportResults], actual: Union[ClearResults, ReportResults]
) -> list[str]:
    """Return a line for each result of a macro that differs from what the README states: expected, then actual."""
    actual_values = actual._asdict()
    return [
        f"The {macro_label} macro, {name.replace('_', ' ')}: expected {value}, got {actual_values.get(name)}."
        for name, value in expected._asdict().items()
        if actual_values.get(name) != value
    ]
