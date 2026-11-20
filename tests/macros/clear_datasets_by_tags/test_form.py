"""Tests of the macro form, runnable.json: its parameters agree with the code."""

from core.tags import (
    INCLUDE_ALL_DATASETS,
    INCLUDE_CHOICES,
    INCLUDE_LABEL,
    INCLUDE_TAGS,
    MATCH_ANY,
    MATCH_CHOICES,
)
from macros.clear_datasets_by_tags import MACRO
from macros.clear_datasets_by_tags.clearing import OPTION_DEFAULTS, OPTION_LABELS
from support.forms import named_params, read_form

# The parameters of the form, top to bottom.
INCLUDED_TAG_PARAMS = ["included_tags", "included_category_tags", "included_match"]
TAG_PARAMS = ["included_scope", *INCLUDED_TAG_PARAMS]
TAG_PARAMS += ["excluded_tags", "excluded_category_tags", "excluded_match"]
OPTION_PARAMS = ["simulate", "purge_shared", "purge_partitioned", "purge_without_recipe"]
COMMON_PARAMS = ["on_error", "recap_to_dataset", "recap_dataset", "recap_append", "on_recap_error"]


def test_the_parameters_in_their_order() -> None:
    form = read_form(MACRO.id)

    assert list(named_params(form)) == TAG_PARAMS + OPTION_PARAMS + COMMON_PARAMS
    assert form["params"][0]["name"] == "included_scope"  # "Include" and the tags come first, in no section.
    assert form["permissions"] == ["WRITE_CONF"]
    assert form["paramsPythonSetup"] == "tag_choices.py"


def test_each_tag_list_starts_from_its_own_empty_list() -> None:
    # A DSS form once sent a tag picked in one list in both: each list gets its own default.
    params = named_params(read_form(MACRO.id))

    for name in ["included_tags", "excluded_tags"]:
        assert (params[name]["type"], params[name]["defaultValue"]) == ("STRINGS", [])
    for name in ["included_category_tags", "excluded_category_tags"]:
        param = params[name]
        assert (param["type"], param["getChoicesFromPython"], param["disableAutoReload"]) == ("MULTISELECT", True, True)
        assert param["defaultValue"] == []


def test_each_match_list_has_the_choices_of_the_code() -> None:
    # "Any" and "All", as the user guide and the recap say them: the label of the list names the tags.
    params = named_params(read_form(MACRO.id))

    for name in ["included_match", "excluded_match"]:
        expected = [{"value": value, "label": label} for value, label in MATCH_CHOICES.items()]
        assert params[name]["selectChoices"] == expected, name
        assert params[name]["defaultValue"] == MATCH_ANY, name


def test_option_defaults_and_labels_match_the_code() -> None:
    params = named_params(read_form(MACRO.id))

    for option, default in OPTION_DEFAULTS.items():
        assert params[option]["defaultValue"] is default, option
    for option, label in OPTION_LABELS.items():
        assert params[option]["label"] == label, option


def test_include_has_the_choices_of_the_code_and_hides_the_included_tags() -> None:
    params = named_params(read_form(MACRO.id))
    scope = params["included_scope"]

    assert (scope["type"], scope["label"], scope["defaultValue"], scope["mandatory"]) == (
        "SELECT",
        INCLUDE_LABEL,
        INCLUDE_TAGS,
        True,
    )
    assert scope["selectChoices"] == [{"value": value, "label": label} for value, label in INCLUDE_CHOICES.items()]
    # "!=": a form without the value, such as one DSS remembered before "Include" existed, still shows the tags.
    for name in INCLUDED_TAG_PARAMS:
        assert params[name]["visibilityCondition"] == f"model.included_scope != '{INCLUDE_ALL_DATASETS}'", name
