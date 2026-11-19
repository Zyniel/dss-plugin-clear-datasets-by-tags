# An excluded tag on no dataset is only a notice

With "All datasets", the excluded tags are the only protection, so a typo in one of them, such as `kep` for `keep`, clears every dataset it should keep. We considered making each excluded tag on no dataset a blocker of the real run (issue #9, PR #11), and rejected it. A project can define a standing rule, "All datasets, except the datasets with `Preserve`", and run it in a scenario while no dataset has `Preserve` for a while. That is not an error, and a blocker would turn the scenario red. So an excluded tag on no dataset stays a yellow notice that names it, the run goes on, and its outcome does not change.

## Consequences

- With "All datasets", a typo in an excluded tag clears the datasets it should protect. The guard is the simulation: the user guide asks to check that each dataset to keep is "Excluded" before a real run.
- With a standing protecting tag, the yellow notice shows on every run where no dataset has the tag.
