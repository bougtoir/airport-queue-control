# GATE 09 — CLEAN REPRODUCIBILITY ON ONE VM

Verdict: **PASS**

Clean git-worktree rebuild of commit 04f589521: fresh venv, `pip install -e '.[dev]'`,
`make all` completed end-to-end. Plan lock hash identical (36114b51…). Final manuscript
docx byte-identical; all reported values identical; CI endpoints differ only at ~1e-12
(float summation order). 52 tests pass in the clean env. See REPRODUCIBILITY_AUDIT.md.

Commit: gate-09 reproducibility audit.
