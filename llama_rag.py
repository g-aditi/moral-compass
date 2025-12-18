"""Lightweight wrapper to generate LLM analyses for submitted form answers.

This module exposes generate_report(form_answers) which performs RAG retrieval
and optional LLM calls. Heavy model loading is done lazily inside the function
so importing this module does not trigger long-running work.
"""

import os
import logging
from typing import List
import time
import json
import hashlib
from math import sqrt


def safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in (s or 'report'))


def generate_report(form_answers: List[str]) -> str:
    """Generate a plain-text analysis for the provided answers.

    Returns the path to the generated report file. This function logs progress to
    `llm_analyses/report_generation.log` and writes per-question analysis to a
    text file in `llm_analyses/`.
    """
    llm_analyses_dir = './llm_analyses'
    os.makedirs(llm_analyses_dir, exist_ok=True)

    # configure module-local logger
    log_path = os.path.join(llm_analyses_dir, 'report_generation.log')
    logger = logging.getLogger('llama_rag')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(fh)
        # also stream to stdout for Flask console
        logger.addHandler(logging.StreamHandler())

    logger.info('Starting report generation')
    # ------------------ ENV VAR CHECK ------------------
    # For security, do NOT hardcode API keys in source. Instead ensure the
    # `ANTHROPIC_API_KEY` env var is set in the shell that starts Flask.
    # If it's not set, log a helpful message and continue (code will fall
    # back to placeholders or other providers).
    try:
        if not os.getenv('ANTHROPIC_API_KEY'):
            logger.warning('ANTHROPIC_API_KEY not set in environment. Export it before starting the server to enable Anthropic API calls.')
        # ensure LLM_PROVIDER defaults to 'anthropic' if the user hasn't set it
        os.environ['LLM_PROVIDER'] = os.getenv('LLM_PROVIDER', 'anthropic')
    except Exception:
        logger.exception('Failed to check Anthropic env vars')
    # ----------------------------------------------------
    
    # --- simple file-based cache for LLM responses ---
    cache_path = os.path.join(llm_analyses_dir, 'llm_cache.json')
    def _load_cache():
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as fh:
                    return json.load(fh)
        except Exception:
            logger.exception('Failed to load cache file; continuing without cache')
        return {}

    def _save_cache(c):
        try:
            with open(cache_path, 'w', encoding='utf-8') as fh:
                json.dump(c, fh, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception('Failed to write cache file')

    cache = _load_cache()

    def _cache_key(prompt_text: str, context_text: str) -> str:
        h = hashlib.sha256()
        h.update((prompt_text or '').encode('utf-8'))
        h.update(b'::')
        h.update((context_text or '').encode('utf-8'))
        return h.hexdigest()

    # --- embedding batching helper (tries sentence-transformers then falls back) ---
    def _batch_embeddings(texts: List[str]):
        # returns list of lists (float vectors) same order as texts
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            vecs = model.encode(texts, show_progress_bar=False)
            return [list(map(float, v)) for v in vecs]
        except Exception:
            logger.info('sentence-transformers unavailable; using simple token-count embeddings')
            # simple fallback: token-count vector over a small vocabulary
            vocab = {}
            vecs = []
            for t in texts:
                toks = [w.lower() for w in t.split() if w.isalpha()]
                ctr = {}
                for w in toks:
                    if w not in vocab:
                        vocab[w] = len(vocab)
                    ctr[vocab[w]] = ctr.get(vocab[w], 0) + 1
                vecs.append((ctr, len(toks)))
            # convert sparse counters to dense vectors (size = vocab)
            size = max(vocab.values()) + 1 if vocab else 0
            dense = []
            for ctr, total in vecs:
                v = [0.0] * size
                for w, idx in vocab.items():
                    v[idx] = float(ctr.get(idx, 0)) / (total or 1)
                dense.append(v)
            return dense

    def _cosine_sim(a, b):
        # simple cosine similarity for two dense lists
        if not a or not b:
            return 0.0
        sa = sum(x * x for x in a)
        sb = sum(y * y for y in b)
        if sa == 0 or sb == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        return dot / (sqrt(sa) * sqrt(sb))

    # --- simple LLM API wrapper (Anthropic preferred, fallback to OpenAI if available) ---
    def _call_llm(prompt: str, max_tokens: int = 512, stream: bool = False) -> str:
        # check cache first
        try:
            key = _cache_key(prompt, '')
            if key in cache:
                logger.info('LLM cache hit')
                return cache[key]['response']
        except Exception:
            logger.exception('Cache lookup failed; continuing')

        # prefer Anthropic (Claude) if configured
        provider = os.getenv('LLM_PROVIDER', '').lower()
        if provider == 'anthropic' and os.getenv('ANTHROPIC_API_KEY'):
            try:
                try:
                    import anthropic
                    client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
                    # Anthropic/Claude expects prompts with turn markers. If the
                    # incoming `prompt` is a plain string, wrap it in the
                    # required format: (optional system) + "\n\nHuman: ...\n\nAssistant:"
                    anth_prompt = prompt
                    try:
                        # normalize whitespace and ensure the prompt STARTS with the
                        # Anthropic conversation marker. If it already starts with
                        # a Human turn, keep it but ensure an Assistant marker at the end.
                        if not isinstance(anth_prompt, str):
                            anth_prompt = str(anth_prompt)
                        norm = anth_prompt.lstrip()
                        if not norm.startswith('\n\nHuman:'):
                            # no space after 'Human:' to match Anthropic's strict turn markers
                            anth_prompt = "\n\nHuman:" + norm
                        else:
                            anth_prompt = norm
                        if not anth_prompt.rstrip().endswith('\n\nAssistant:'):
                            anth_prompt = anth_prompt + "\n\nAssistant:"
                    except Exception:
                        # be defensive; fall back to original prompt if wrapping fails
                        logger.exception('Failed to format prompt for Anthropic; using original prompt')

                    # debug: write the full anth_prompt to a local debug file so we
                    # can inspect exact bytes sent to Anthropic (local-only).
                    try:
                        debug_path = os.path.join(llm_analyses_dir, 'debug_anthropic_prompt.txt')
                        with open(debug_path, 'w', encoding='utf-8') as dbg:
                            dbg.write(anth_prompt)
                        logger.info('Wrote Anthropic debug prompt to %s', debug_path)
                    except Exception:
                        logger.exception('Failed to write Anthropic debug prompt')

                    # use a compact completion call where available
                    # Try a small list of candidate model names (the account may not have access
                    # to every model name). If the env var ANTHROPIC_MODEL is set, try it first.
                    model_env = os.getenv('ANTHROPIC_MODEL')
                    candidates = []
                    if model_env:
                        candidates.append(model_env)
                    # common Anthropic model names to try (order is intentionally conservative)
                    candidates.extend(['claude-2', 'claude-3', 'claude-instant-v1', 'claude-instant-1'])
                    last_exc = None
                    for m in candidates:
                        try:
                            logger.info('Trying Anthropic model (Messages API): %s', m)
                            # Use the Messages API (modern) rather than Completions.
                            resp = client.messages.create(
                                model=m,
                                messages=[{"role": "user", "content": anth_prompt}],
                                max_tokens=max_tokens,
                            )

                            # Extract response text robustly from different SDK return shapes
                            def _extract_anthropic_text(r):
                                try:
                                    # Common SDK: Message object with .content list of TextBlock-like objects
                                    if hasattr(r, 'content') and isinstance(r.content, (list, tuple)):
                                        parts = []
                                        for blk in r.content:
                                            # blk may be a dict-like or object with .text
                                            if isinstance(blk, dict):
                                                t = blk.get('text') or blk.get('content') or ''
                                            else:
                                                t = getattr(blk, 'text', None) or getattr(blk, 'content', None) or str(blk)
                                            if isinstance(t, (list, tuple)):
                                                # nested content blocks
                                                t = ' '.join(x.get('text') if isinstance(x, dict) else str(x) for x in t)
                                            parts.append(t)
                                        return '\n'.join(p for p in parts if p)

                                    # Older shapes: resp.message may be dict or object
                                    if hasattr(r, 'message') and r.message:
                                        msg = r.message
                                        if isinstance(msg, dict):
                                            # message.content may be list
                                            cont = msg.get('content') or msg.get('text')
                                            if isinstance(cont, list):
                                                return '\n'.join((c.get('text') if isinstance(c, dict) else str(c)) for c in cont)
                                            if isinstance(cont, str):
                                                return cont
                                            return str(msg)
                                        else:
                                            # object-like
                                            if hasattr(msg, 'content'):
                                                parts = []
                                                for blk in getattr(msg, 'content'):
                                                    parts.append(getattr(blk, 'text', str(blk)))
                                                return '\n'.join(parts)
                                            return str(msg)

                                    # Fallbacks
                                    if hasattr(r, 'completion') and r.completion:
                                        return r.completion
                                    if isinstance(r, dict):
                                        # try common dict keys
                                        text = r.get('completion') or r.get('text')
                                        if text:
                                            return text
                                        out = r.get('output') or r.get('choices')
                                        if isinstance(out, list) and out:
                                            first = out[0]
                                            if isinstance(first, dict):
                                                return first.get('content') or first.get('text') or str(first)
                                        return str(r)
                                except Exception:
                                    pass
                                # As a last resort, try to parse the string repr for TextBlock text fields
                                s = str(r)
                                try:
                                    import re
                                    matches = re.findall(r'text=(?:"([^"]*)"|\'([^\']*)\')', s, flags=re.S)
                                    if matches:
                                        parts = [m[0] or m[1] for m in matches]
                                        return '\n'.join(p for p in parts if p)
                                except Exception:
                                    pass
                                return s

                            text = _extract_anthropic_text(resp)

                            # Normalize string reprs (if SDK returned an object string) by extracting
                            # any TextBlock text=... occurrences so we store readable assistant text.
                            try:
                                if isinstance(text, str) and ("Message(" in text or "TextBlock(" in text or "content=[" in text):
                                    import re
                                    matches = re.findall(r'text=(?:"([^"]*)"|\'([^\']*)\')', text, flags=re.S)
                                    if matches:
                                        parts = [a or b for a,b in matches]
                                        text = '\n'.join(p for p in parts if p)
                            except Exception:
                                pass
                            cache[key] = {'response': text, 'ts': time.time(), 'provider': f'anthropic-messages:{m}'}
                            _save_cache(cache)
                            return text
                        except Exception as e:
                            logger.warning('Anthropic Messages API model %s failed: %s', m, getattr(e, '__class__', str(e)))
                            last_exc = e
                    # if none of the candidate models worked, re-raise last exception
                    if last_exc:
                        raise last_exc
                except Exception:
                    logger.exception('Anthropic python client failed; attempting HTTP fallback')
                    # If anthropic package not available, try HTTP call (best-effort)
                    import requests
                    url = 'https://api.anthropic.com/v1/complete'
                    headers = {'x-api-key': os.getenv('ANTHROPIC_API_KEY'), 'Content-Type': 'application/json'}
                    body = {
                        'model': os.getenv('ANTHROPIC_MODEL', 'claude-2'),
                        'prompt': anth_prompt,
                        'max_tokens_to_sample': max_tokens,
                    }
                    try:
                        # log a short preview of the body for debugging
                        try:
                            body_preview = json.dumps({'model': body.get('model'), 'prompt': body.get('prompt')[:200]})
                        except Exception:
                            body_preview = str({'model': body.get('model')})
                        logger.info('Anthropic HTTP body preview: %s', body_preview)
                    except Exception:
                        pass
                    # Try HTTP fallback across a set of model candidates
                    model_env = os.getenv('ANTHROPIC_MODEL')
                    candidates = []
                    if model_env:
                        candidates.append(model_env)
                    candidates.extend(['claude-2', 'claude-3', 'claude-instant-v1', 'claude-instant-1'])
                    last_exc = None
                    for m in candidates:
                        # For the Messages HTTP endpoint, send a messages array
                        body = {
                            'model': m,
                            'messages': [{ 'role': 'user', 'content': anth_prompt }],
                            'max_tokens': max_tokens,
                        }
                        try:
                            # log a short preview of the body for debugging
                            try:
                                body_preview = json.dumps({'model': body.get('model'), 'messages': (body.get('messages')[0].get('content') or '')[:200]})
                            except Exception:
                                body_preview = str({'model': body.get('model')})
                            logger.info('Anthropic HTTP body preview: %s', body_preview)
                            r = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=body, timeout=30)
                            logger.info('Anthropic HTTP response status: %s', r.status_code)
                            logger.info('Anthropic HTTP response body (preview): %s', (r.text or '')[:500])
                            r.raise_for_status()
                            j = r.json()
                            # Try common response shapes
                            text = None
                            if isinstance(j, dict):
                                text = j.get('completion') or j.get('text')
                                if not text:
                                    # new messages responses might contain 'output' or 'choices'
                                    out = j.get('output') or j.get('choices')
                                    if isinstance(out, list) and out:
                                        first = out[0]
                                        if isinstance(first, dict):
                                            text = first.get('content') or first.get('text') or first.get('message') or None
                            if not text:
                                text = str(j)
                            # Normalize any Message/TextBlock reprs in the HTTP response
                            try:
                                if isinstance(text, str) and ("Message(" in text or "TextBlock(" in text or "content=[" in text):
                                    import re
                                    matches = re.findall(r'text=(?:"([^"]*)"|\'([^\']*)\')', text, flags=re.S)
                                    if matches:
                                        parts = [a or b for a,b in matches]
                                        text = '\n'.join(p for p in parts if p)
                            except Exception:
                                pass
                            cache[key] = {'response': text, 'ts': time.time(), 'provider': f'anthropic-http:{m}'}
                            _save_cache(cache)
                            return text
                        except Exception as e:
                            logger.warning('Anthropic HTTP model %s failed: %s', m, getattr(e, '__class__', str(e)))
                            last_exc = e
                    if last_exc:
                        raise last_exc
            except Exception:
                logger.exception('Anthropic API call failed; falling back')

        # fallback to OpenAI if available
        try:
            if os.getenv('OPENAI_API_KEY'):
                try:
                    import openai
                    openai.api_key = os.getenv('OPENAI_API_KEY')
                    resp = openai.Completion.create(model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                                                     prompt=prompt,
                                                     max_tokens=max_tokens)
                    text = resp.choices[0].text if resp and resp.choices else str(resp)
                    cache[key] = {'response': text, 'ts': time.time(), 'provider': 'openai'}
                    _save_cache(cache)
                    return text
                except Exception:
                    logger.exception('OpenAI call failed')
        except Exception:
            logger.exception('OpenAI fallback path failed')

        # last resort: no provider available
        logger.info('No LLM provider available; returning placeholder')
        return 'LLM unavailable or failed; no analysis generated.'
    # Lazy imports and model/index loads (catch failures and continue with placeholders)
    documents_text = []
    doc2vec_model = None
    index = None
    try:
        from vectordb_storage import documents_text as _documents_text
        documents_text = _documents_text
    except Exception as e:
        logger.warning(f'Could not import vectordb_storage.documents_text: {e}')

    try:
        # Prefer FAISS + sentence-transformers retrieval when available. This will
        # load a pre-built `vector_db.faiss` and `docs_meta.json` (created by
        # scripts/reindex.py). If absent, fallback to simple document text.
        import faiss
        import numpy as np
        # load existing faiss index and docs metadata if present
        docs_meta = None
        if os.path.exists('docs_meta.json'):
            try:
                with open('docs_meta.json', 'r', encoding='utf-8') as fh:
                    docs_meta = json.load(fh)
                    documents_text = [d.get('text', '') for d in docs_meta]
                logger.info('Loaded docs_meta.json with %d entries', len(documents_text))
            except Exception:
                logger.exception('Failed to load docs_meta.json; continuing')

        if os.path.exists('vector_db.faiss'):
            try:
                index = faiss.read_index('vector_db.faiss')
                logger.info('Loaded FAISS index')
            except Exception:
                logger.exception('Failed to read vector_db.faiss; index unavailable')
        else:
            logger.info('FAISS index not found; retrieval will use document text fallback')

        def retrieve_context(query, top_k=3):
            try:
                if index is None:
                    return '\n\n'.join(documents_text[:top_k]) if documents_text else ''

                # embed the query using sentence-transformers (same model used for reindexing)
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    q_emb = model.encode([query], show_progress_bar=False)
                except Exception:
                    logger.exception('sentence-transformers unavailable for query embedding; falling back to text')
                    return '\n\n'.join(documents_text[:top_k]) if documents_text else ''

                qv = np.array(q_emb, dtype='float32')
                # normalize vector for inner-product (index built with normalized vectors)
                faiss.normalize_L2(qv)
                D, I = index.search(qv, top_k)
                relevant = []
                for idx in I[0]:
                    if 0 <= idx < len(documents_text):
                        relevant.append(documents_text[idx])
                    elif docs_meta and 0 <= idx < len(docs_meta):
                        relevant.append(docs_meta[idx].get('text', ''))
                return '\n\n'.join(relevant)
            except Exception:
                logger.exception('Error during retrieve_context; falling back to empty context')
                return ''

    except Exception:
        # If faiss or other libs unavailable, provide a fallback retrieve_context
        logger.exception('Could not initialize retrieval stack (faiss/sentence-transformers)')

        def retrieve_context(query, top_k=3):
            return '\n\n'.join(documents_text[:top_k]) if documents_text else ''

    # try to initialize local HF LLM pipeline lazily, but skip if an API provider is configured
    pipe = None
    system_context_from_faiss = retrieve_context('Belmont Report, IRB Guidelines, How should an IRB function?')
    try:
        provider = os.getenv('LLM_PROVIDER', '').lower()
        # if an external API provider is set (anthropic/openai) prefer that and avoid local HF model init
        if provider in ('anthropic', 'openai'):
            logger.info(f'LLM_PROVIDER={provider}; skipping local transformers pipeline initialization')
            pipe = None
        else:
            from transformers import pipeline
            import torch
            model_id = 'meta-llama/Meta-Llama-3.1-8B-Instruct'
            device = 0 if torch.cuda.is_available() else -1
            logger.info(f'Initializing pipeline (device cuda? {torch.cuda.is_available()})')
            pipe = pipeline('text-generation', model=model_id, device=device)
    except Exception:
        logger.exception('LLM pipeline initialization failed; analyses will contain placeholders')
        pipe = None

    # build output filename
    title = (form_answers[0] if form_answers and form_answers[0] else 'report')
    filename = safe_filename(title)
    output_filepath = os.path.join(llm_analyses_dir, f"{filename}-llm-analysis.txt")

    try:
        # We'll perform retrieval -> rerank -> LLM call per question, using batching where appropriate
        with open(output_filepath, 'w', encoding='utf-8') as file:
            for idx, answer in enumerate(form_answers or []):
                q = f'Question {idx+1}'
                logger.info(f'Processing question {idx+1}')

                # initial retrieval (top_k candidates)
                initial_ctx = []
                try:
                    raw = retrieve_context(q, top_k=10)
                    # if retrieve_context returns concatenated text, split into candidate chunks heuristically
                    if isinstance(raw, str):
                        # naive split into paragraphs
                        cand = [p.strip() for p in raw.split('\n\n') if p.strip()]
                        if not cand and raw:
                            # fallback split by sentence/lines
                            cand = [line.strip() for line in raw.splitlines() if line.strip()]
                        initial_ctx = cand[:10]
                    elif isinstance(raw, list):
                        initial_ctx = raw[:10]
                except Exception:
                    logger.exception('Initial retrieval failed; using global documents')
                    initial_ctx = documents_text[:10]

                # if we have no candidates, use a small set of global docs
                if not initial_ctx:
                    initial_ctx = documents_text[:5]

                # rerank candidates using embeddings (batch)
                try:
                    texts_to_embed = [q] + initial_ctx
                    emb = _batch_embeddings(texts_to_embed)
                    q_vec = emb[0]
                    cand_vecs = emb[1:]
                    sims = [_cosine_sim(q_vec, c) for c in cand_vecs]
                    ranked = [x for _, x in sorted(zip(sims, initial_ctx), key=lambda t: t[0], reverse=True)]
                    top_ctx = ranked[:5]
                except Exception:
                    logger.exception('Reranking failed; using unranked candidates')
                    top_ctx = initial_ctx[:5]

                prompt_context = '\n\n'.join(top_ctx)
                nett_input = f"Context: {prompt_context}\n\nQuestion: {q}\n\nAnswer: {answer}"

                # prefer API-backed LLM if available; else try HF pipeline loaded earlier (pipe)
                llm_response_text = None
                try:
                    # check cache and call API-backed LLM
                    llm_response_text = _call_llm(nett_input, max_tokens=512)
                    # If cache gave us placeholder, continue to HF pipeline fallback
                    if llm_response_text and 'LLM unavailable or failed' not in llm_response_text:
                        logger.info(f'LLM (API) provided response for question {idx+1}')
                except Exception:
                    logger.exception('API LLM call failed')

                if (not llm_response_text or 'LLM unavailable or failed' in llm_response_text) and pipe is not None:
                    try:
                        outputs = pipe(nett_input, max_new_tokens=256, do_sample=True)
                        if isinstance(outputs, list) and outputs:
                            llm_response_text = outputs[0].get('generated_text') or str(outputs[0])
                        else:
                            llm_response_text = str(outputs)
                    except Exception:
                        logger.exception(f'LLM pipeline failed for question {idx+1}')

                if not llm_response_text:
                    llm_response_text = 'LLM unavailable or failed; no analysis generated.'

                file.write(f'Question {idx+1}: {q}\n')
                file.write(f'Answer: {answer}\n')
                file.write(f'LLM Response: {llm_response_text}\n\n')

        logger.info(f'Wrote analysis to {output_filepath}')
        # Also try to write a PDF version for easier sharing/viewing if reportlab is available
        try:
            pdf_path = os.path.splitext(output_filepath)[0] + '.pdf'
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                styles = getSampleStyleSheet()
                doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                story = []
                with open(output_filepath, 'r', encoding='utf-8') as fh:
                    for line in fh:
                        line = line.rstrip()
                        if not line:
                            story.append(Spacer(1, 6))
                        else:
                            # Use preformatted-like Paragraph to preserve simple newlines
                            story.append(Paragraph(line.replace('  ', '&nbsp;&nbsp;'), styles['Normal']))
                doc.build(story)
                logger.info('Wrote PDF analysis to %s', pdf_path)
            except Exception:
                logger.exception('Failed to write PDF (reportlab not available or error)')
        except Exception:
            logger.exception('PDF generation step failed')
    except Exception:
        logger.exception('Failed to write analysis file')

    return output_filepath
