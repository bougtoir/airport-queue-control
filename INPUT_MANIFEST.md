# INPUT_MANIFEST — SMPT retarget, Gate 0 (input freeze)

Date: 2026-10-13 UTC. Working tree: bougtoir/wip `airport-batch-queue/`, branch
`devin/1791902486-airport-smpt-retarget` (created from master after PR #634 merge).

## Authoritative inputs

| Input | Path | Version/date | SHA-256 | Note |
|---|---|---|---|---|
| Latest author-approved main manuscript (QC'd) | manuscript/qc/manuscript_author_FINAL.docx | git 19a3b50f9 | 16d6823b2806a20dbb54868616e116faf36a5c57998780d433be44720a0134c9 | Final QC build; 102 automated checks PASS. Selected as authoritative text source. |
| Generated manuscript source | manuscript/manuscript.md | builder scripts/build_phase11_manuscript.py | 6ca7b126e577216de482c03d0e9832343f9d4f4479a43e1f04682c7aefb76ce5 | Markdown master; QC docx derives from it. |
| Generated manuscript docx (pre-QC) | manuscript/manuscript.docx | 4ccdc61650ecbbba73c365493ecb501f9e880f1fcc7dcea62663b2d101e4169f | Superseded by QC version for reading; builder remains canonical. |
| Locked analysis plan | ANALYSIS_PLAN_LOCKED.yaml (+ .sha256 sidecar) | v1.1 frozen | 36114b51e3f10e7708fac6867faca8fd246cbff4e0eec53dbda9656d7070619c | Sidecar verified against plan earlier (see prior audits). |
| Locked primary results | results/phase5/primary_results.csv | fd80a08b078333002f8b54f519b3b18dd3a1c3ce0c9fd55029c4242f9094954f | 200 paired replications, loads 0.85/0.95, CRN. |
| Precision ledger | results/phase5/monte_carlo_precision.csv | 4131869756d31ea6486a2de655673e0faa16a40ab4d89ae7fadd2b2eb031543c | Target 0.100; achieved 0.439/1.087. |
| Paired comparisons | results/phase5/paired_comparisons.csv | 4e0b275ba4c00d4b724283f4ac6e4a9a935c187a8b5279dbae8fa0f39f8adc57 | |
| Seed ledger | results/phase5/seeds.csv | 8863eb505617c7a1f119f5070ce1417695c43f113d1317e8e1fe2e470d103c3f | |
| Run manifest | results/phase5/run_manifest.json | abbdfcfb020b0dedbf2c9006ff1fb209676dcf5a1f64e324307c92567e85b780 | |
| Verified references ledger | references/verified_references.csv | 24 rows | 20 cited + records; Crossref-verified. |
| Parameter provenance | references/parameter_sources.csv | 23 rows | configs/default.yaml is truth for 0.04/0.55/0.97. |
| TR-C submission files | submission/ (cover_letter.docx/md, highlights.txt, graphical_abstract.png, TRC_SUBMISSION_CHECKLIST.md, PACKAGE_MANIFEST.csv) | a34e9487c1b53aecfd3df11600eaa009cc13baff9f8a26585f9e93200c5e7761 (cover_letter.docx); 3eca5cf3fa83f1291a7259ee6baa8fbca98bde8da6ba365df599284e23819bc4 (highlights) | TR-C-specific; to be replaced, not reused verbatim. |
| TR-C guide snapshot | data/raw/official/trc_guide_for_authors_2026-09-24_full.* | 2026-09-24 | Prior journal's rules; reference only. |
| Prior audits | TRACEABILITY_AUDIT.md, CONSISTENCY_AUDIT.md, REPRODUCIBILITY_AUDIT.md, NUMBERING_QC.md, FIGURE_TABLE_CROSSREFERENCE_AUDIT.csv, manuscript_values.csv, HOSTILE_TR_C_REVIEW.md, TRC_SCOPE_AUDIT.md | repo HEAD | Baseline QC evidence. |
| Handoff document | HANDOFF_airport_queue_after_TRC_reject.md (attachment) | 2026-10-13 | Frozen values, sync rules, constraints. |
| Gate prompt | SMPT_gated_revision_single_VM.txt (attachment) | 2026-10-13 | Execution contract. |

## Conflicts / gaps

- `manuscript_author(2).docx` (named in the prompt) is not present on this machine or in
  the repo. `manuscript/qc/manuscript_author_FINAL.docx` (commit 19a3b50f9) is the newest
  author-approved build and is selected as authoritative.
- No TR-C rejection letter file exists in the repo or attachments. The rejection reason is
  recorded only in the gate prompt: "insufficient theoretical development and
  emerging-technology implications for TR-C". Treated as the only prescreening evidence.
- Previously copied unrelated declarations were already fixed (dispensing-data consent/ethics
  text replaced with simulation-specific statements; see FINAL_HANDOFF.md).

PASS — authoritative inputs selected and hashed; original scientific record documented.
