# Runbook - Lab Day 10

## Symptom

Users or agents may see stale or incomplete retrieval answers, for example refund policy says "14 ngay" instead of 7 days, HR annual leave says 10 days instead of 12 days, or Level 4 Admin Access cannot be retrieved because `access_control_sop` was not published.

## Detection

- Check the latest log in `artifacts/logs/` for `PIPELINE_HALT`, expectation failures, and record counts.
- Check `artifacts/eval/grading_run.jsonl`; every grading row should have `contains_expected=true`, `hits_forbidden=false`, and `top1_doc_matches=true` when an expected doc id is defined.
- Check freshness in `artifacts/manifests/manifest_day10-final.json`. The sample run returns `FAIL` because `latest_exported_at=2026-04-11T00:00:00` is older than the 24-hour SLA on 2026-06-10.

## Diagnosis

| Step | Action | Expected result |
|---|---|---|
| 1 | Open `artifacts/manifests/manifest_day10-final.json` | Confirm `run_id`, raw/clean/quarantine counts, and index path. |
| 2 | Open `artifacts/quarantine/quarantine_day10-final.csv` | Confirm invalid rows have explicit reasons. |
| 3 | Run `uv run python eval_retrieval.py --out artifacts/eval/after_fix_eval.csv` | All 21 test questions should contain expected terms and avoid forbidden terms. |
| 4 | Run `uv run python grading_run.py --out artifacts/eval/grading_run.jsonl` | All 10 grading rows should pass. |

## Mitigation

Fix the source export or cleaning rule, rerun `uv run python etl_pipeline.py run --run-id day10-final`, then rerun eval and grading. If a stale publish was intentional for demonstration, use a distinct run id such as `inject-bad` and do not leave that index as the final state.

## Prevention

Keep `ALLOWED_DOC_IDS` synchronized with the contract, require halt expectations for stale policy content, and review quarantine reason counts in every run. Use Chroma in a fully provisioned environment; the current workspace uses `artifacts/simple_index/day10_kb.json` as a deterministic fallback when Chroma is unavailable.
