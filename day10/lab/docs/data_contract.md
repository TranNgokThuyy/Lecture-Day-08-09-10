# Data Contract - Lab Day 10

Source of truth: `contracts/data_contract.yaml`

## 1. Source Map

| Source | Ingest method | Main failure mode | Metric / alert |
|---|---|---|---|
| `policy_refund_v4` | Raw CSV export from policy catalog | Stale 14-day refund window | `refund_no_stale_14d_window` halt |
| `sla_p1_2026` | Raw CSV export from incident system | Missing or malformed effective date | quarantine reason count |
| `it_helpdesk_faq` | Raw CSV export from helpdesk FAQ | Duplicate chunks and empty text | `duplicate_chunk_text`, `missing_chunk_text` |
| `hr_leave_policy` | Raw CSV export from HR system | 2025 annual leave text mixed into 2026 export | `stale_hr_2025_content`, `hr_leave_no_stale_10d_annual` |
| `access_control_sop` | Raw CSV export from IT Security SOP | Valid source omitted from allowlist | `required_doc_ids_present` halt |

## 2. Cleaned Schema

| Column | Type | Required | Notes |
|---|---|---|---|
| `chunk_id` | string | yes | Stable id for publish/upsert. |
| `doc_id` | string | yes | Must be in the allowed canonical doc list. |
| `chunk_text` | string | yes | Minimum length 8 and not ambiguous placeholder content. |
| `effective_date` | date | yes | Normalized to `YYYY-MM-DD`; `DD/MM/YYYY` input is accepted and normalized. |
| `exported_at` | datetime | yes | Must be ISO parseable for freshness lineage. |

## 3. Quarantine vs Drop

Rows are not silently dropped. Invalid rows are written to `artifacts/quarantine/quarantine_<run-id>.csv` with a `reason` field such as `unknown_doc_id`, `stale_hr_2025_content`, `invalid_exported_at_format`, `ambiguous_content`, or `duplicate_chunk_text`. Re-introduction requires source-owner approval and a rerun with a visible log/manifest.

## 4. Version and Canonical Policy

Current canonical sources are the five allowed doc ids in `contracts/data_contract.yaml`: refund v4, SLA P1 2026, IT Helpdesk FAQ, HR leave policy 2026, and access control SOP. HR annual-leave content must align with the 2026 policy, and refund requests must use the 7-business-day v4 window.
