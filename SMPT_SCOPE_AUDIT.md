# SMPT_SCOPE_AUDIT — Gate 1 (checked 2026-10-13 UTC, official Elsevier pages)

Sources (persisted):
- data/raw/official/smpt_guide_for_authors_2026-10-13_full.html (SHA-256
  8befc6dfdd580efeef948674f017c831f2c655c41784cf34d6bfe4dcda719fa0)
- Journal page + Guide for Authors (rendered DOM 2026-10-13)

## Aims and scope (verbatim key points)
- Forum for original high-quality papers on any aspect of systems simulation and modelling.
- Solicits: theoretical aspects (formal modelling, model-checking, RNG, sensitivity analysis,
  variance reduction, experimental design, meta-modelling, V&V methods, selection/comparison
  procedures); methodology and applications incl. transportation systems.
- Application papers must make model development, implementation, mathematical/scalability
  problems and validation/verification transparent.

## Fit assessment
- This paper is a DES methodology + application study: explicit event/state/control
  formalization, V&V (10 internal checks), sensitivity/falsification design, optimization
  grid, reproducible code. Fits "methodology and application of modelling and simulation in
  transportation systems" and "experimental design / sensitivity analysis / V&V methods".
- TR-C-specific "emerging technology" framing must be removed — SMPT has no such requirement.

## Editorial and publication facts
- Single-anonymized review; Editor-in-Chief Angelo Furfaro (Univ. of Calabria).
- Submission via Editorial Manager (SIMPAT).
- Subscription route: NO publication fee charged to authors (official journal page,
  verified 2026-10-13). OA option APC USD 3,110 — not required. PASS on no-mandatory-APC.
- Current article type: research article (no special article-type constraints found).
- Yuan et al. 2025 appeared in SMPT special issue "Advancements in Simulation Modeling of
  Pedestrian Dynamics and Crowd Evacuation" — the journal demonstrably publishes airport
  checkpoint pedestrian simulation.

## Format requirements (Guide for Authors, current)
- Editable file: .doc/.docx (single column) or .tex; remove strikethrough/underline.
- Title page: title, author names, affiliations (lowercase superscript letters), corresponding
  author + email; present/permanent address footnotes.
- Abstract: ≤250 words, standalone, no references, define abbreviations.
- Keywords: 1–7, English.
- Highlights: encouraged, 3–5 bullets ≤85 chars each, separate editable file named with
  "highlights".
- Math: editable text, solidus for small fractions, italic variables, exp notation, numbered
  display equations in citation order.
- Tables: editable text, numbered by appearance, captions, notes below, no vertical
  rules/shading; place next to relevant text or at end.
- Figures: separate files recommended (EPS/PDF vector, ≥300 dpi photos, ≥1000 dpi line art),
  each cited and numbered in order; captions mandatory; text graphics may be embedded.
- Article structure: numbered sections/subsections.
- References: numbered [n] in order of appearance; any consistent style accepted at
  submission; Elsevier author-initial style applied at proof; DOIs encouraged.
- Research data: **Option C — REQUIRED** to deposit data in a repository and cite/link, or
  explain why not. Public repo https://github.com/bougtoir/airport-queue-control covers code;
  data statement required at submission.
- Declarations: competing interests via Elsevier declarations tool (docx upload);
  standard funding sentence; generative-AI statement section before references (if used);
  simulation-only work needs no human-subjects ethics statement.
- No explicit word limit found for regular research articles.

## Verdict
Journal fit: **suitable** for a simulation-methodology contribution, provided the manuscript
is repositioned as transparent DES modelling/V&V/experimentation rather than emerging
technology. No mandatory APC (subscription route confirmed).
