# Individual Report - Lab Day 10

**Name:** PLACEHOLDER_STUDENT  
**Role:** Cleaning, Quality, Embed fallback, and Evidence  
**run_id:** `day10-final`

## Responsibility

I worked on the Day 10 data pipeline inside `Lecture-Day-08-09-10/day10/lab`. The main files touched were `transform/cleaning_rules.py`, `quality/expectations.py`, `etl_pipeline.py`, `eval_retrieval.py`, `grading_run.py`, and the documentation/report files. The goal was to make the pipeline publish only current, valid chunks and produce evidence that retrieval quality improves after cleaning.

## Technical Decision

The most important decision was to treat stale policy content as a halt-level data quality issue. The baseline filtered HR rows by effective date, but some HR 2025 content still had 2026 dates and survived cleaning. I added `stale_hr_2025_content` so chunks containing stale annual-leave text such as `10 ngày phép năm` are quarantined even when the date field looks valid. I also added `required_doc_ids_present` because the grading set requires `access_control_sop`; without that expectation, the pipeline could exit with an incomplete corpus.

## Anomaly and Fix

The first baseline run produced 247 raw records, 40 cleaned records, 207 quarantine records, and halted on `hr_leave_no_stale_10d_annual` with 2 violations. After the fix, `day10-final` produced 247 raw records, 37 cleaned records, and 210 quarantine records. New measurable quarantine impacts included 6 `stale_hr_2025_content`, 5 `ambiguous_content`, and 7 `invalid_exported_at_format` rows.

## Before / After Evidence

The inject run `inject-bad` used `--no-refund-fix --skip-validate`. It failed `refund_no_stale_14d_window` with 2 violations and `artifacts/eval/after_inject_bad.csv` showed `q_refund_window` had `hits_forbidden=yes`. The clean run `day10-final` wrote `artifacts/eval/after_fix_eval.csv`, where all 21 test questions returned `contains_expected=yes`, `hits_forbidden=no`, and `top1_doc_expected=yes`.

Official grading is stored in `artifacts/eval/grading_run.jsonl`. All 10 rows pass, including `gq_d10_09` for HR annual leave and `gq_d10_10` for Level 4 Admin Access.

## Two-hour Improvement

The next improvement would be to provision Chroma and the SentenceTransformers model in CI so the same tests run against the production vector backend. This workspace used `artifacts/simple_index/day10_kb.json` as a deterministic fallback because Chroma installation did not complete.
