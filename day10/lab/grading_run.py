#!/usr/bin/env python3
"""
Chạy bộ câu grading (retrieval + keyword) — output JSONL cho giảng viên.

  python grading_run.py --out artifacts/eval/grading_run.jsonl

Yêu cầu: đã chạy `python etl_pipeline.py run` trước để có collection Chroma.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--questions",
        default=str(ROOT / "data" / "grading_questions.json"),
    )
    p.add_argument(
        "--out",
        default=str(ROOT / "artifacts" / "eval" / "grading_run.jsonl"),
    )
    p.add_argument("--top-k", type=int, default=10)
    args = p.parse_args()

    qpath = Path(args.questions)
    qs = json.loads(qpath.read_text(encoding="utf-8"))
    db_path = os.environ.get("CHROMA_DB_PATH", str(ROOT / "chroma_db"))
    collection_name = os.environ.get("CHROMA_COLLECTION", "day10_kb")
    model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    query = None
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=db_path)
        emb = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        col = client.get_collection(name=collection_name, embedding_function=emb)
        from simple_retrieval import rerank_result

        query = lambda text, n_results: rerank_result(
            col.query(query_texts=[text], n_results=max(n_results * 4, 10)),
            text,
            top_k=n_results,
        )
    except Exception as e:
        from simple_retrieval import query_index

        index_path = ROOT / "artifacts" / "simple_index" / f"{collection_name}.json"
        if not index_path.is_file():
            print(f"Collection/index error: {e}", file=sys.stderr)
            print(f"Fallback index not found: {index_path}", file=sys.stderr)
            return 2
        query = lambda text, n_results: query_index(index_path, text, top_k=n_results)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        for q in qs:
            text = q["question"]
            res = query(text, args.top_k)
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            blob = " ".join(docs).lower()
            must_any = [x.lower() for x in q.get("must_contain_any", [])]
            forbidden = [x.lower() for x in q.get("must_not_contain", [])]
            ok_any = any(m in blob for m in must_any) if must_any else True
            bad_forb = any(m in blob for m in forbidden) if forbidden else False
            top_doc = (metas[0] or {}).get("doc_id", "") if metas else ""
            want_top1 = (q.get("expect_top1_doc_id") or "").strip()
            top1_ok = True
            if want_top1:
                top1_ok = top_doc == want_top1
            rec = {
                "id": q.get("id"),
                "question": text,
                "top1_doc_id": top_doc,
                "contains_expected": ok_any,
                "hits_forbidden": bad_forb,
                "top1_doc_matches": top1_ok if want_top1 else None,
                "top_k_used": args.top_k,
                "grading_criteria": q.get("grading_criteria", []),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
