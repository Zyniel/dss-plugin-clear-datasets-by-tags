# Clear Datasets by Tags

A plugin for Dataiku (DSS) with macros to maintain a project: one clears the data of the datasets that match tag rules, one reports how the datasets use tags.

## Plugin and macros

**Plugin**:
Clear Datasets by Tags, the DSS plugin that holds the macros. Say "the plugin", or "the Clear Datasets by Tags plugin", never its name alone.
_Avoid_: DSS Project Maintenance

**Macro**:
One of the project maintenance macros of the plugin: the Clear Datasets by Tags macro or the Report Dataset Tags macro. Say "the <name> macro", never its name alone.

**Macro that changes data**:
A macro that can change the data of the project, such as the Clear Datasets by Tags macro. It has "Simulate", checked by default.
_Avoid_: destructive macro, write macro

**Macro that only reads**:
A macro that changes nothing in the project but its summary dataset, such as the Report Dataset Tags macro. It has no "Simulate".
_Avoid_: read-only macro

## Runs

**Simulation**:
A run of a macro that changes data, with "Simulate" checked. It changes nothing, and shows what a real run would do.
_Avoid_: dry run, test run

**Real run**:
A run of a macro that changes data, with "Simulate" unchecked.
_Avoid_: live run, actual run

**Blocked run**:
A real run that a blocker stops before anything changes.
_Avoid_: stopped run, aborted run

**Stopped run**:
A real run that stops at its first failed clear, because "If an error occurs" is "Raise exception". The datasets after it are not tried.
_Avoid_: blocked run, aborted run

**Outcome**:
How a run ends: SUCCESS, WARNING (problems, and the run goes on, so DSS shows a success) or FAILED (the run ends in error).
_Avoid_: result, status

**Notice**:
Something the reader of a recap must know, while the run goes on.
_Avoid_: warning, info

**Blocker**:
A reason a real run must stop, found before anything changes. A simulation shows it, and goes on.
_Avoid_: error, failed check

**Problem**:
A failure of the work, or of the summary dataset. The problems of a run set its outcome.
_Avoid_: warning, error

## Datasets

**Dataset of the project**:
A dataset that the project owns. A run scans all of them, and only them.
_Avoid_: local dataset

**Foreign dataset**:
A dataset of another project, shared into this one. No macro handles it.
_Avoid_: shared dataset, imported dataset

**Shared dataset**:
A dataset of the project that it shares with other projects. Clearing it can break them.
_Avoid_: exposed dataset

**External dataset**:
A dataset whose data DSS does not manage, such as a SQL table created outside DSS. It is never cleared.
_Avoid_: unmanaged dataset

**Partitioned dataset**:
A dataset whose data is split into partitions. Clearing it clears every partition.

**Dataset with no recipe**:
A dataset that no recipe of the Flow builds: once cleared, nothing can rebuild its data.
_Avoid_: source dataset, input dataset

**Untagged dataset**:
A dataset with no tag.

**Summary dataset**:
The dataset of the project that a run writes its recap to, when its form asks for it. It is never cleared.
_Avoid_: recap dataset, report dataset

## Clearing

**Clear**:
Delete the data of a dataset, every partition included, and keep its definition, schema and settings.
_Avoid_: purge, clean up, empty, truncate, drop, delete

**Tag rules**:
The part of a form that says which datasets a macro takes and which it leaves: "Include", the included tags and the excluded tags, each list with its match.
_Avoid_: tag selection, filter, criteria

**Include**:
The choice of the tag rules that says which datasets are selected: the datasets with the included tags, or all datasets.
_Avoid_: scope

**Selected dataset**:
A dataset that "Include" takes: a dataset with the included tags, or every dataset with "All datasets". An excluded dataset is selected too.
_Avoid_: matched dataset, target

**Protection**:
A reason that keeps a selected dataset from being cleared. The protections apply in a fixed order, and the first one wins: the excluded tags (the dataset is excluded), then the summary dataset, an external dataset, or an option (the dataset is skipped).
_Avoid_: rule

**Excluded dataset**:
A selected dataset that matches the excluded tags. It is never cleared.

**Dataset to clear**:
A selected dataset that no protection keeps. A simulation marks it "Cleared (Simulate)". A real run clears it, fails to, or stops before it.
_Avoid_: candidate, target

**Skipped dataset**:
A selected dataset, not excluded, that the run did not try to clear. Either a protection kept it (it is the summary dataset, it is external, or an option keeps it), or it is not tried. Its reason says which.
_Avoid_: ignored dataset

**Not tried**:
The reason of a skipped dataset that a stopped run never reached. Without the stop, it would have been cleared.
_Avoid_: pending, protected

**Risk**:
What can break when a dataset to clear is cleared: it is shared, partitioned, or has no recipe.
_Avoid_: warning

**Status**:
What a recap says about one of its rows, such as Cleared, Failed, Skipped or Excluded for a dataset, or Used and Unknown for a tag.
_Avoid_: outcome, state

## Tags

**Form tag**:
A tag typed or picked in the included or the excluded list of a form.
_Avoid_: filter, selector

**Match**:
How a list of form tags matches a dataset: "Any" (the dataset has at least one of them) or "All" (it has every one).

**Tag category**:
A category of tags, with its values, that a DSS administrator defines, such as `Stage` with `Raw` and `Output`.
_Avoid_: category tag

**Category tag**:
A tag written `<category>:<value>`, such as `Stage:Raw`.
_Avoid_: tag category

**Unknown tag**:
A category tag whose category or value is not in the tag categories of DSS. Often a typo.
_Avoid_: invalid tag

**Project tag list**:
The tags of a project, on any of its objects: datasets, but also recipes or notebooks.

**Unused tag**:
A tag of the project tag list that no dataset has. It can still be on a recipe.
_Avoid_: tag on no dataset

**Form tag on no dataset**:
A form tag that no dataset of the project has. It selects nothing, or excludes nothing.
_Avoid_: unused tag

## Recap

**Recap**:
What a run gives: an HTML page, with the same content as JSON.
_Avoid_: report, summary, result

**Banner**:
A coloured block of a recap that shows a notice, a blocker, a problem or the outcome. It is only how the recap shows them, not a concept of its own.
_Avoid_: alert, message
