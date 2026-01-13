# Moral Compass - Project Structure

## Core Application Files

### Main Pipeline
- **llama_rag.py** - Main RAG pipeline with Ollama integration
- **app.py** - Flask web application
- **form_responses.py** - IRB form question definitions

### Data & Models
- **docs_meta.json** - IRB document metadata (22 documents)
- **vector_db.faiss** - FAISS vector database index
- **txt_documents/** - Source IRB guideline documents

### Configuration
- **requirements.txt** - Python dependencies
- **.python-version** - Python version specification
- **.gitignore** - Git ignore rules

## Documentation

- **README.md** - Project overview and setup instructions
- **METHODOLOGY.md** - Complete technical methodology (architecture, algorithms, design)
- **QUALITY_EVALUATION_REPORT.md** - Comprehensive quality assessment and validation

## Testing

- **comprehensive_test_with_eval.py** - Complete 13-question test with quality metrics

## Analysis Output

### llm_analyses/
- **Study on the Impact of AI-Assisted Learning Tools...txt** - Latest comprehensive IRB analysis (77 KB, 13 questions, 121 citations)
- **llm_cache.json** - Response cache for efficiency
- **report_generation.log** - Processing logs

## Web Interface

### static/
- CSS and JavaScript files for web interface

### templates/
- HTML templates for Flask application

## Utilities

### scripts/
- **reindex.py** - Vector database reindexing utility
- **pdf_to_text.py** - PDF conversion utility

## Virtual Environments (not tracked in git)

- **.venv/** - Python 3.13 virtual environment
- **.venv310/** - Python 3.10 virtual environment
- **.venv311/** - Python 3.11 virtual environment

## System Files

- **.git/** - Git repository
- **__pycache__/** - Python bytecode cache
- **.ipynb_checkpoints/** - Jupyter notebook checkpoints

---

## Cleaned Up (Removed)

The following files were removed to reduce clutter:

### Removed Test Files
- test_ollama_integration.py
- test_citations.py
- test_formatting.py
- generate_test_report.py
- end_to_end_test.py
- final_test.py
- extract_clean_responses.py

### Removed Documentation
- FINAL_SUMMARY.md (consolidated into QUALITY_EVALUATION_REPORT.md)
- SETUP_COMPLETE.md (consolidated into README.md)
- OLLAMA_SETUP.md (consolidated into METHODOLOGY.md)

### Removed Old Reports
- All intermediate test reports (keeping only latest comprehensive report)
- Old smoke test outputs
- Formatting test outputs

---

## Quick Start

1. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Run comprehensive test:**
   ```bash
   python3 comprehensive_test_with_eval.py
   ```

3. **Start web application:**
   ```bash
   python3 app.py
   ```

4. **View latest analysis:**
   ```bash
   cat "llm_analyses/Study on the Impact of AI-Assisted Learning Tools on Student Performance in Undergraduate Computer Science Courses-llm-analysis.txt"
   ```

---

**Last Updated:** January 13, 2026
**Status:** Production Ready ✅
**Quality Score:** 9/9 (100%)
