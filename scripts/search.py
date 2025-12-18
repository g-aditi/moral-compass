"""Simple CLI to query the FAISS index built by scripts/reindex.py

Usage:
  source .venv/bin/activate
  python scripts/search.py "your query here" --k 5

Prints the top-k document filenames and snippets.
"""
import argparse
from pathlib import Path
import json

p = argparse.ArgumentParser()
p.add_argument('query', help='Query string')
p.add_argument('--k', type=int, default=5)
args = p.parse_args()

INDEX = Path('vector_db.faiss')
META = Path('docs_meta.json')

if not INDEX.exists() or not META.exists():
    raise SystemExit('vector_db.faiss and docs_meta.json must exist. Run scripts/reindex.py first.')

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

with open(META, 'r', encoding='utf-8') as fh:
    docs = json.load(fh)

index = faiss.read_index(str(INDEX))
model = SentenceTransformer('all-MiniLM-L6-v2')
qemb = model.encode([args.query], show_progress_bar=False)
qv = np.array(qemb, dtype='float32')
faiss.normalize_L2(qv)
D, I = index.search(qv, args.k)
for rank, idx in enumerate(I[0]):
    if 0 <= idx < len(docs):
        meta = docs[idx]
        snippet = (meta.get('text') or '')[:400].replace('\n', ' ')
        print(f"{rank+1}. {meta.get('filename')} (score={D[0][rank]:.4f})\n   {snippet}\n")
