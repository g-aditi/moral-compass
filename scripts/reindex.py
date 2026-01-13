"""Reindex documents: compute embeddings with sentence-transformers and build a FAISS index.

Outputs:
- vector_db.faiss         (FAISS index file)
- docs_meta.json         (JSON list of dicts: {id, filename, text})

Usage:
  source .venv/bin/activate
  python scripts/reindex.py --docs-dir txt_documents --out-index vector_db.faiss --out-meta docs_meta.json

"""
from pathlib import Path
import json
import argparse

BATCH = 64
EMB_MODEL = 'all-MiniLM-L6-v2'


def load_text_files(d: Path):
    files = sorted([p for p in d.glob('**/*') if p.is_file() and p.suffix.lower() in ('.txt',)])
    docs = []
    for p in files:
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            try:
                text = p.read_text(encoding='latin-1')
            except Exception:
                text = ''
        # store filename and a friendly source name (just the filename without path)
        docs.append({
            'id': len(docs), 
            'filename': str(p), 
            'source': p.name,  # short filename for citations
            'text': text
        })
    return docs


def compute_embeddings(model, texts, batch_size=BATCH):
    out = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = model.encode(batch, show_progress_bar=False)
        out.extend([list(map(float, v)) for v in emb])
    return out


def build_faiss_index(embs):
    try:
        import faiss
    except Exception as e:
        raise RuntimeError('faiss is required to build index') from e
    import numpy as np
    # convert to float32 matrix
    mat = np.array(embs, dtype='float32')
    # normalize for cosine similarity (inner-product after normalize)
    import numpy.linalg as la
    norms = la.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    mat = mat / norms
    d = mat.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(mat)
    return index


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--docs-dir', default='txt_documents')
    p.add_argument('--out-index', default='vector_db.faiss')
    p.add_argument('--out-meta', default='docs_meta.json')
    p.add_argument('--model', default=EMB_MODEL)
    args = p.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        raise SystemExit(f'docs dir not found: {docs_dir}')

    print('Loading documents...')
    docs = load_text_files(docs_dir)
    print(f'Found {len(docs)} documents')
    texts = [d['text'] or '' for d in docs]

    print(f'Loading embedding model: {args.model} (sentence-transformers)')
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise SystemExit('sentence-transformers is required. Install with: pip install sentence-transformers')

    model = SentenceTransformer(args.model)
    print('Computing embeddings...')
    embs = compute_embeddings(model, texts)

    print('Building FAISS index...')
    index = build_faiss_index(embs)

    print(f'Writing index to {args.out_index}...')
    try:
        import faiss
        faiss.write_index(index, args.out_index)
    except Exception as e:
        raise SystemExit('Failed to write faiss index: ' + str(e))

    print(f'Writing metadata to {args.out_meta}...')
    with open(args.out_meta, 'w', encoding='utf-8') as fh:
        json.dump(docs, fh, ensure_ascii=False, indent=2)

    print('Reindex complete.')


if __name__ == '__main__':
    main()
