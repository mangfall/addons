# Agent instructions — MANGFALL Apps (public)

Binding first: the company repository standard
[mission-control/REPO_STANDARD.md](https://github.com/mangfall/mission-control/blob/main/REPO_STANDARD.md)
and the "Hard rules for all agents" in
[mission-control/README.md](https://github.com/mangfall/mission-control/blob/main/README.md).
Where this file and the standard disagree, the standard wins; this file only adds repo-specific rules.

## This repository is public
- Never commit real Home Assistant data, entity names from real homes, IPs, tokens or customer data.
  Test fixtures stay anonymised.
- Nothing in code, comments or commits may point to an AI provider or to internal tools.
- No links to private repositories in customer-facing text.

## Language
- Repo text in English. Customer-facing text in German: card strings, add-on `README.md`, `DOCS.md`,
  `CHANGELOG.md`, add-on log messages, the "Für Kunden" section of the top-level README.

## Cards
- Every card must show something useful without configuration, load fast, look calm, and never show a red
  error box. The MANGFALL mark links to https://mangfall.eu/karten and stays discreet.
- The cards must not send data anywhere and must not show unsolicited advertising.
- A new card or option must also be added to Haglo Assist (its copy of the file, `MANGFALL_CARDS` in
  `server.py` and its prompt) so both stay in sync.

## Before calling anything done
- `node mangfall-cards/tests/cards.test.mjs` and
  `python3 -m unittest discover -s mangfall-cards/tests -p 'test_*.py'` green; `ruff format --check` clean.
- Test on the owner's development Home Assistant first, then release.
- No `git push` or tag without the CEO's go.
