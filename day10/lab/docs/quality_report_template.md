# Quality Report - Lab Day 10

**run_id:** `day10-final`  
**Date:** 2026-06-10  
**Inject run:** `inject-bad`

## 1. Data Summary

| Metric | Before / inject | After | Notes |
|---|---:|---:|---|
| raw_records | 247 | 247 | Same source CSV. |
| cleaned_records | 37 | 37 | Cleaning keeps the same clean volume after refund inject because inject disables text fix only. |
| quarantine_records | 210 | 210 | Final reasons include stale HR, invalid exported_at, ambiguous content, duplicates, and unknown docs. |
| Expectation halt? | yes | no | Inject fails `refund_no_stale_14d_window`; final run passes all halt expectations. |

## 2. Before / After Retrieval

Evidence files:

- `artifacts/eval/after_inject_bad.csv`
- `artifacts/eval/after_fix_eval.csv`
- `artifacts/eval/grading_run.jsonl`

Key row: `q_refund_window`

| Run | top1_doc_id | contains_expected | hits_forbidden | top1_doc_expected |
|---|---|---|---|---|
| inject-bad | `policy_refund_v4` | yes | yes | yes |
| day10-final | `policy_refund_v4` | yes | no | yes |

The final eval also passes HR versioning and access-control retrieval: `q_hr_annual_leave_under3` top1 is `hr_leave_policy`, and `q_access_level4` top1 is `access_control_sop`.

## 3. Freshness and Monitor

Freshness status for `day10-final` is `FAIL` because the newest sample export timestamp is `2026-04-11T00:00:00`, while the run date is 2026-06-10 and the SLA is 24 hours. This is expected for the static lab data and is documented as a data-snapshot freshness failure, not a pipeline execution failure.

## 4. Corruption Inject

The inject command was `uv run python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`. It intentionally published refund chunks without replacing the stale "14 ngay lam viec" window. The expectation suite detected 2 refund violations, and `after_inject_bad.csv` shows `hits_forbidden=yes` for `q_refund_window`.

## 5. Limits and Follow-up

- Chroma was unavailable in this workspace, so a standard-library lexical fallback index was used and documented in the manifest.
- A production setup should provision Chroma and the SentenceTransformers model before scheduled runs.
