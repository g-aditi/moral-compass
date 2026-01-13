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
    # Default to Ollama for local, no-API-key inference
    # Set LLM_PROVIDER environment variable to override (e.g., 'anthropic', 'openai')
    try:
        # Default to 'ollama' if no provider is explicitly set
        os.environ['LLM_PROVIDER'] = os.getenv('LLM_PROVIDER', 'ollama')
        # Default to Llama 3.2 8B Instruct model (no API required, fully local)
        os.environ['OLLAMA_MODEL'] = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
        logger.info(f'Using LLM provider: {os.environ["LLM_PROVIDER"]} with model: {os.environ.get("OLLAMA_MODEL", "N/A")}')
    except Exception:
        logger.exception('Failed to set LLM provider env vars')
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

        # provider selection
        provider = os.getenv('LLM_PROVIDER', '').lower()

        # Support local Ollama (primary option for no-API-key usage)
        if provider == 'ollama':
            # Try Python ollama client first, then fall back to CLI 'ollama run'
            model = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
            try:
                try:
                    import ollama
                    logger.info(f'Using Ollama Python client with model: {model}')
                    # ollama.chat returns a dict-like object or string depending on client
                    try:
                        resp = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])

                        # Extract ONLY the clean text content - ollama returns ChatResponse object
                        text = None

                        # Try to get content from response object attributes (ollama >= 0.6.0)
                        if hasattr(resp, 'message') and hasattr(resp.message, 'content'):
                            text = resp.message.content
                        # Fallback for dict-like responses (older versions)
                        elif isinstance(resp, dict):
                            if 'message' in resp and isinstance(resp['message'], dict):
                                text = resp['message'].get('content', '')
                            else:
                                text = resp.get('content') or resp.get('output')

                        if text and isinstance(text, str):
                            # Cache the clean text only (no metadata)
                            cache[key] = {'response': text, 'ts': time.time(), 'provider': f'ollama-python:{model}'}
                            _save_cache(cache)
                            logger.info('Ollama Python client returned clean response')
                            return text
                        else:
                            logger.warning(f'Could not extract content from response type: {type(resp)}')
                    except Exception as e:
                        # if python client shape differs, fall through to CLI
                        logger.warning(f'Ollama Python client failed: {e}')
                        pass
                except Exception as e:
                    logger.warning(f'Could not import ollama Python client: {e}')
                    pass

                # Fallback to CLI: `ollama run <model>` (sends prompt on stdin)
                import subprocess
                logger.info(f'Falling back to Ollama CLI with model: {model}')
                cmd = ['ollama', 'run', model]
                p = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=120)
                if p.returncode == 0:
                    text = p.stdout.strip() or p.stderr.strip() or ''
                    if text:
                        cache[key] = {'response': text, 'ts': time.time(), 'provider': f'ollama-cli:{model}'}
                        _save_cache(cache)
                        logger.info('Ollama CLI returned response')
                        return text
                else:
                    logger.warning('ollama CLI failed: %s', p.stderr)
            except Exception as e:
                logger.exception('ollama provider failed: %s', str(e))

        # prefer Anthropic (Claude) if configured
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

                    # Use the single configured Anthropic model with rate limit backoff
                    model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            logger.info('Trying Anthropic model (Messages API): %s (attempt %d/%d)', model, attempt + 1, max_retries)
                            # Use the Messages API (modern) rather than Completions.
                            resp = client.messages.create(
                                model=model,
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
                            cache[key] = {'response': text, 'ts': time.time(), 'provider': f'anthropic-messages:{model}'}
                            _save_cache(cache)
                            return text
                        except Exception as e:
                            # If rate limit, wait and retry
                            if 'RateLimitError' in str(type(e).__name__) or 'rate' in str(e).lower():
                                wait_time = 30 + (attempt * 10)  # 30s, 40s, 50s for retries
                                logger.warning('Rate limit hit; waiting %d seconds before retry', wait_time)
                                time.sleep(wait_time)
                                if attempt < max_retries - 1:
                                    continue
                            # If last attempt or non-rate-limit error, raise
                            logger.error('Anthropic Messages API failed: %s', str(e))
                            raise
                except Exception as e:
                    # No HTTP fallback - just fail cleanly
                    logger.exception('Anthropic Messages API failed after %d attempts', max_retries)
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
    # Note: legacy vectordb_storage has been removed. We now rely solely on
    # docs_meta.json and vector_db.faiss built by scripts/reindex.py.

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
            """Return list of dicts with 'text', 'source', and 'score' keys."""
            try:
                if index is None:
                    # fallback: return documents with generic source info
                    results = []
                    for i, txt in enumerate(documents_text[:top_k]):
                        src = docs_meta[i].get('source', f'Document {i+1}') if docs_meta and i < len(docs_meta) else f'Document {i+1}'
                        results.append({'text': txt, 'source': src, 'score': 0.0})
                    return results

                # embed the query using sentence-transformers (same model used for reindexing)
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    q_emb = model.encode([query], show_progress_bar=False)
                except Exception:
                    logger.exception('sentence-transformers unavailable for query embedding; falling back to text')
                    results = []
                    for i, txt in enumerate(documents_text[:top_k]):
                        src = docs_meta[i].get('source', f'Document {i+1}') if docs_meta and i < len(docs_meta) else f'Document {i+1}'
                        results.append({'text': txt, 'source': src, 'score': 0.0})
                    return results

                qv = np.array(q_emb, dtype='float32')
                # normalize vector for inner-product (index built with normalized vectors)
                faiss.normalize_L2(qv)
                D, I = index.search(qv, top_k)
                results = []
                for score, idx in zip(D[0], I[0]):
                    if 0 <= idx < len(documents_text):
                        txt = documents_text[idx]
                        src = docs_meta[idx].get('source', f'Document {idx+1}') if docs_meta and idx < len(docs_meta) else f'Document {idx+1}'
                        results.append({'text': txt, 'source': src, 'score': float(score)})
                    elif docs_meta and 0 <= idx < len(docs_meta):
                        txt = docs_meta[idx].get('text', '')
                        src = docs_meta[idx].get('source', f'Document {idx+1}')
                        results.append({'text': txt, 'source': src, 'score': float(score)})
                return results
            except Exception:
                logger.exception('Error during retrieve_context; falling back to empty context')
                return []

    except Exception:
        # If faiss or other libs unavailable, provide a fallback retrieve_context
        logger.exception('Could not initialize retrieval stack (faiss/sentence-transformers)')

        def retrieve_context(query, top_k=3):
            """Return list of dicts with 'text', 'source', and 'score' keys."""
            results = []
            for i, txt in enumerate(documents_text[:top_k] if documents_text else []):
                results.append({'text': txt, 'source': f'Document {i+1}', 'score': 0.0})
            return results

    # try to initialize local HF LLM pipeline lazily, but skip if an API provider or Ollama is configured
    pipe = None
    system_context_from_faiss = retrieve_context('Belmont Report, IRB Guidelines, How should an IRB function?')
    try:
        provider = os.getenv('LLM_PROVIDER', '').lower()
        # if an external provider (anthropic/openai/ollama) is set, skip HF transformers pipeline
        # Ollama is preferred for local inference as it's much faster and easier to use
        if provider in ('anthropic', 'openai', 'ollama'):
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

                # initial retrieval (top_k candidates) - now returns list of dicts
                initial_results = []
                try:
                    initial_results = retrieve_context(q, top_k=10)
                except Exception:
                    logger.exception('Initial retrieval failed; using global documents')
                    for i, txt in enumerate(documents_text[:10]):
                        initial_results.append({'text': txt, 'source': f'Document {i+1}', 'score': 0.0})

                # if we have no candidates, use a small set of global docs
                if not initial_results:
                    for i, txt in enumerate(documents_text[:5]):
                        initial_results.append({'text': txt, 'source': f'Document {i+1}', 'score': 0.0})

                # rerank candidates using embeddings (batch) while preserving source metadata
                try:
                    texts_to_embed = [q] + [r['text'] for r in initial_results]
                    emb = _batch_embeddings(texts_to_embed)
                    q_vec = emb[0]
                    cand_vecs = emb[1:]
                    sims = [_cosine_sim(q_vec, c) for c in cand_vecs]
                    # sort by similarity, keeping full result dicts
                    ranked_results = [x for _, x in sorted(zip(sims, initial_results), key=lambda t: t[0], reverse=True)]
                    top_results = ranked_results[:5]
                except Exception:
                    logger.exception('Reranking failed; using unranked candidates')
                    top_results = initial_results[:5]

                # build context text and source citations
                prompt_context = '\n\n'.join([r['text'] for r in top_results])
                sources_used = [r['source'] for r in top_results]

                # Create source reference list for the prompt
                source_refs = '\n'.join([f"[{i+1}] {src}" for i, src in enumerate(sources_used)])

                # Enhanced prompt that instructs LLM to cite sources
                irb_prompt = f"""You are an IRB (Institutional Review Board) compliance expert. Analyze the following study information using the provided context documents.

Context Documents (cite these using [1], [2], etc.):
{source_refs}

Relevant Content:
{prompt_context}

Question: {q}
Answer: {answer}

Instructions:
1. Identify key ethical considerations and potential IRB compliance issues
2. Reference the context documents when applicable using citations like [1], [2]
3. Highlight any concerns or strengths in the protocol
4. Be specific and actionable in your analysis

Analysis:"""

                nett_input = irb_prompt

                # prefer API-backed LLM if available; else try HF pipeline loaded earlier (pipe)
                llm_response_text = None
                try:
                    # check cache and call API-backed LLM (increased to 512 for proper citations and analysis)
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

                # Format the output with clear sections and proper line breaks
                file.write(f'\n{"="*80}\n')
                file.write(f'QUESTION {idx+1}\n')
                file.write(f'{"="*80}\n\n')

                file.write(f'USER INPUT:\n')
                file.write(f'{"-"*80}\n')
                file.write(f'{answer.strip()}\n')
                file.write(f'{"-"*80}\n\n')

                file.write(f'IRB COMPLIANCE ANALYSIS:\n')
                file.write(f'{"-"*80}\n')
                # Ensure proper line breaks in analysis
                formatted_analysis = llm_response_text.strip()
                file.write(f'{formatted_analysis}\n')
                file.write(f'{"-"*80}\n\n')

                file.write(f'REFERENCES & SOURCES:\n')
                file.write(f'{"-"*80}\n')
                for i, src in enumerate(sources_used, 1):
                    file.write(f'  [{i}] {src}\n')
                file.write(f'{"-"*80}\n\n')

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
