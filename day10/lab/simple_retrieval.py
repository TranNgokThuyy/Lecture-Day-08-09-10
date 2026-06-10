from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List


_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) >= 2]


def _score(question: str, document: str, metadata: Dict[str, Any] | None, *, pos: int) -> float:
    q_tokens = _tokens(question)
    q_set = set(q_tokens)
    d_tokens = _tokens(document)
    d_set = set(d_tokens)
    overlap = sum(1 for t in q_tokens if t in d_set)
    phrase_bonus = 0
    q_lower = (question or "").lower()
    d_lower = (document or "").lower()
    for phrase in ("level 4", "p1", "vpn", "finance team", "dưới 3 năm", "standard access"):
        if phrase in q_lower and phrase in d_lower:
            phrase_bonus += 4

    doc_id = ((metadata or {}).get("doc_id") or "").strip()
    doc_bonus = 0
    doc_hints = (
        ("sla_p1_2026", ("p1", "sla", "ticket p1", "sự cố p1", "escalate", "phản hồi", "resolution")),
        ("policy_refund_v4", ("hoàn tiền", "refund", "finance team")),
        ("it_helpdesk_faq", ("vpn", "mật khẩu", "tài khoản", "email", "hộp thư")),
        ("hr_leave_policy", ("phép", "nghỉ", "nhân viên", "kinh nghiệm")),
        ("access_control_sop", ("access", "quyền", "level", "admin", "ciso")),
    )
    for hinted_doc, hints in doc_hints:
        if doc_id == hinted_doc and any(h in q_lower for h in hints):
            doc_bonus += 8

    return overlap + phrase_bonus + doc_bonus + (len(q_set & d_set) / math.sqrt(max(len(d_set), 1))) - (pos * 0.001)


def rerank_result(result: Dict[str, List[List[Any]]], question: str, *, top_k: int) -> Dict[str, List[List[Any]]]:
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    pairs = []
    for pos, doc in enumerate(docs):
        meta = metas[pos] if pos < len(metas) else {}
        pairs.append((_score(question, doc or "", meta or {}, pos=pos), doc or "", meta or {}))
    pairs.sort(key=lambda x: x[0], reverse=True)
    top = pairs[:top_k]
    return {
        "documents": [[doc for _score_value, doc, _meta in top]],
        "metadatas": [[meta for _score_value, _doc, meta in top]],
    }


def write_index(index_path: Path, rows: List[Dict[str, Any]], *, run_id: str) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "rows": [
            {
                "id": r.get("chunk_id", ""),
                "document": r.get("chunk_text", ""),
                "metadata": {
                    "doc_id": r.get("doc_id", ""),
                    "effective_date": r.get("effective_date", ""),
                    "run_id": run_id,
                },
            }
            for r in rows
        ],
    }
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def query_index(index_path: Path, question: str, *, top_k: int) -> Dict[str, List[List[Any]]]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    rows = payload.get("rows") or []
    scored = []
    for pos, row in enumerate(rows):
        doc = row.get("document") or ""
        score = _score(question, doc, row.get("metadata") or {}, pos=pos)
        scored.append((score, -pos, row))

    scored.sort(reverse=True)
    top = [row for score, _pos, row in scored[:top_k] if score > 0]
    if not top:
        top = [row for _score, _pos, row in scored[:top_k]]
    return {
        "documents": [[r.get("document") or "" for r in top]],
        "metadatas": [[r.get("metadata") or {} for r in top]],
    }
