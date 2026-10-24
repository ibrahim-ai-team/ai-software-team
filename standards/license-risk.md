# License risk for generated and reused code

## Policy

Generated code is not automatically license-free. Before adopting copied, adapted, or generated code that may reproduce an existing implementation, identify its source and license. Do not introduce code under an incompatible or unapproved license without explicit legal/owner review.

### Prohibited by default

- **GPL-3.0** (including GPL-3.0-only and GPL-3.0-or-later).
- **AGPL** (all versions), including AGPL-3.0-only and AGPL-3.0-or-later.
- Any dependency or source whose license is unknown or whose terms cannot be verified: block release until clarified.

These are repository policy restrictions, not a claim that these licenses are universally incompatible with every project. A specific exception requires documented owner approval and compatibility review.

### Generally permitted (subject to notices and obligations)

- MIT
- Apache-2.0
- BSD-2-Clause and BSD-3-Clause
- ISC
- Python Software Foundation License (PSF)
- Unlicense / CC0-1.0 for code where applicable

MPL-2.0 and other weak-copyleft, source-available, custom, dual, or non-standard licenses require case-by-case review before adoption. Preserve copyright notices, license texts, attribution, patent notices and other obligations required by the applicable license.

## Checklist for additions over 50 lines

Before adding or adapting more than 50 lines of non-trivial code from a source, or when generated code appears unusually similar to a known implementation:

- [ ] Record the source URL/repository and the exact file or commit.
- [ ] Identify and verify the source license from authoritative repository/license metadata.
- [ ] Check whether the proposed code reproduces expressive implementation details rather than only behavior, APIs, or general ideas.
- [ ] Compare against the prohibited-license list and review compatibility with this repository's distribution model.
- [ ] Preserve required copyright, attribution, NOTICE and license text.
- [ ] Prefer a clean-room implementation from a behavior-level specification when source provenance is uncertain.
- [ ] Ask the code/security reviewer to record findings and request owner/legal review when uncertain.
- [ ] Do not merge until the risk is resolved and the review evidence is linked in the PR.

The 50-line threshold is a review trigger, not a safe harbor: smaller snippets can also carry license risk.

## Automated dependency check

The repository's `.github/workflows/license-check.yml` runs `scripts/check_licenses.py` on pushes and pull requests. It reports declared Python dependencies and their installed distribution license metadata, fails for prohibited GPL-3.0/AGPL licenses, and fails closed when a declared dependency cannot be verified. This is a lightweight metadata check, not legal advice or source-code similarity detection.
