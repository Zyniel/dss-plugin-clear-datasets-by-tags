# Domain docs

Before exploring an area of the code, read `GLOSSARY.md` and the ADRs of `docs/adr/` that touch it.

## Use the glossary's vocabulary

When your output names a domain concept (an issue title, a refactor proposal, a hypothesis, a test name), use the term as `GLOSSARY.md` defines it, not a synonym it avoids. A concept missing from the glossary is a signal: either the project does not use that language, or there is a gap to resolve with `/domain-modeling`.

## Flag ADR conflicts

When your output contradicts an ADR, say so, with why it is worth reopening:

> _Contradicts ADR-0001 ("Clear shared datasets" is checked by default), but worth reopening because…_
