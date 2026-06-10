# Group Report - Lab Day 10: Data Pipeline & Data Observability

**Group name:** PLACEHOLDER_GROUP  
**Members:**

| Name | Day 10 role | Email |
|---|---|---|
| PLACEHOLDER_STUDENT | Ingestion / Raw Owner | placeholder@example.com |
| PLACEHOLDER_STUDENT | Cleaning & Quality Owner | placeholder@example.com |
| PLACEHOLDER_STUDENT | Embed & Idempotency Owner | placeholder@example.com |
| PLACEHOLDER_STUDENT | Monitoring / Docs Owner | placeholder@example.com |

**Submission date:** 2026-06-10  
**Repo:** PLACEHOLDER_REPO  
**Final run_id:** `day10-final`

## 1. Pipeline Overview

The lab pipeline reads `data/raw/policy_export_dirty.csv`, cleans invalid or stale rows, validates the cleaned snapshot, publishes an index, and writes logs/manifests/eval artifacts. The final command is:

`uv run python etl_pipeline.py run --run-id day10-final`

The final run produced 247 raw records, 37 cleaned records, and 210 quarantine records. The log records `run_id`, `raw_records`, `cleaned_records`, `quarantine_records`, cleaned/quarantine CSV paths, expectation results, index path, manifest path, and freshness status. Chroma was unavailable in this workspace, so the pipeline wrote `artifacts/simple_index/day10_kb.json` as a deterministic fallback; the Chroma upsert/prune path remains supported when dependencies are installed.

## 2. Cleaning and Expectations

The main fixes were to add `access_control_sop` to the valid source allowlist, remove HR 2025 annual-leave content even when its date looked current, quarantine ambiguous placeholder chunks, and block malformed `exported_at` timestamps. The expectation suite now also requires all five grading doc ids to be present, rejects ambiguous content, and verifies exported timestamps are parseable.

### 2a. metric_impact

| New rule / expectation | Before | After / inject | Evidence |
|---|---:|---:|---|
| `access_control_sop` allowlist | 8 rows were treated as `unknown_doc_id` | Access-control questions pass; `gq_d10_10` top1 is `access_control_sop` | `artifacts/eval/grading_run.jsonl` |
| `stale_hr_2025_content` | 2 stale HR chunks survived and `hr_leave_no_stale_10d_annual` failed | 6 rows quarantined; HR expectation passes | `artifacts/quarantine/quarantine_day10-final.csv` |
| `ambiguous_content` | Ambiguous chunks could enter cleaned data | 5 rows quarantined; `no_ambiguous_content` passes | quarantine reason count |
| `invalid_exported_at_format` | Slash-formatted export timestamps could enter lineage | 7 rows quarantined; `exported_at_parseable_iso` passes | quarantine reason count |
| `required_doc_ids_present` | Missing `access_control_sop` was not detected as a halt | Final run passes with `missing=[]` | `artifacts/logs/run_day10-final.log` |

Final quarantine reason counts are: 109 `unknown_doc_id`, 48 `duplicate_chunk_text`, 21 `stale_hr_policy_effective_date`, 8 `missing_chunk_text`, 7 `invalid_exported_at_format`, 6 `missing_effective_date`, 6 `stale_hr_2025_content`, and 5 `ambiguous_content`.

## 3. Before / After Retrieval

The corruption inject command was:

`uv run python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`

That run intentionally skipped the refund text fix and published the bad snapshot. It failed `refund_no_stale_14d_window` with 2 violations but continued because `--skip-validate` was used for the demo. In `artifacts/eval/after_inject_bad.csv`, `q_refund_window` has `contains_expected=yes` and `hits_forbidden=yes`, proving that stale context was still retrievable.

After rerunning the final pipeline, `artifacts/eval/after_fix_eval.csv` has all 21 questions with `contains_expected=yes`, `hits_forbidden=no`, and `top1_doc_expected=yes`. Official grading in `artifacts/eval/grading_run.jsonl` passes all 10 questions, including HR versioning (`gq_d10_09`) and access control (`gq_d10_10`).

## 4. Freshness and Monitoring

The manifest `artifacts/manifests/manifest_day10-final.json` reports `latest_exported_at=2026-04-11T00:00:00`. With `FRESHNESS_SLA_HOURS=24` and current date 2026-06-10, the freshness result is `FAIL`. This is expected for a static lab snapshot and should be interpreted as stale source data, not an ETL crash.

## 5. Day 09 Connection

The Day 09 agent layer should consume only the published current corpus. This Day 10 pipeline makes that safer by removing stale policy chunks before retrieval, preserving run lineage in the manifest, and validating that required source documents are present before the index is used.

## 6. Remaining Risks

- Chroma dependency installation did not complete in this workspace, so verification used the built-in fallback index.
- Placeholder identity fields should be replaced before submission.
- A production run should alert the owning team when freshness fails instead of accepting a stale lab snapshot.

## 7. Peer Review Questions

1. Does the final pipeline prove that every required grading document is present before publish?
2. Does the before/after eval show a real user-facing improvement, not only a cleaner CSV?
3. Are freshness failures explained as data snapshot age rather than ignored pipeline errors?
