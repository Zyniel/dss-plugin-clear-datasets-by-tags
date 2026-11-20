# "Clear shared datasets" is checked by default

To skip the shared datasets, the Clear Datasets by Tags macro must first find them, and reading the sharing of a project needs more rights than the macro asks for ("Write project content"): DSS gives it to project administrators only. So the option is checked by default: a run clears the datasets that match its tag rules without the sharing analysis, and the recap shows each shared dataset as a risk, or says that the sharing was not checked. Unchecked by default, every real run by an editor who is not a project administrator would be blocked.

It is the only option that lets the macro clear risky data and is checked by default: "Clear partitioned datasets" and "Clear datasets with no recipe" are unchecked.

## Consequences

- An API call or a scenario that sends no `purge_shared` value clears shared datasets. Changing the default would change what they do. And DSS keeps the last values of a form in the browser, so users would not all see a new default ([verification](../verification.md), row 26).
- That only project administrators can read the sharing is not in the Dataiku documentation. It is row 13 of [verification](../verification.md): on DSS 13.4.4, an editor who is not a project administrator cannot read it (integration test, 2026-11-20). If a later DSS lets an editor read the sharing, an unchecked default would no longer block editors: reopen this decision.
