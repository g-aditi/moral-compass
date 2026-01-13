"""Convert PDFs to plain text files.

Usage:
  source .venv/bin/activate
  python scripts/pdf_to_text.py --pdf-dir documents --out-dir txt_documents

Notes:
- Requires PyPDF2 (installed).
- Writes one .txt per .pdf, using UTF-8 encoding.
- Skips encrypted/unreadable pages gracefully.
"""
from pathlib import Path
import argparse
import sys

try:
    import PyPDF2
except Exception:
    print("PyPDF2 is required. Install with: pip install PyPDF2", file=sys.stderr)
    raise


def pdf_to_text(pdf_path: Path) -> str:
    text_parts = []
    try:
        with pdf_path.open('rb') as f:
            reader = PyPDF2.PdfReader(f)
            if getattr(reader, 'is_encrypted', False):
                # attempt decrypt empty password if possible
                try:
                    reader.decrypt("")
                except Exception:
                    pass
            for i, page in enumerate(reader.pages):
                try:
                    t = page.extract_text() or ""
                    # normalize whitespace lightly
                    t = t.replace('\r', '\n')
                    text_parts.append(t)
                except Exception:
                    # skip problematic pages
                    text_parts.append("")
    except Exception:
        return ""
    return "\n".join(text_parts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pdf-dir', default='documents')
    p.add_argument('--out-dir', default='txt_documents')
    args = p.parse_args()

    pdf_dir = Path(args.pdf_dir)
    out_dir = Path(args.out_dir)
    if not pdf_dir.exists():
        print(f"PDF directory not found: {pdf_dir}", file=sys.stderr)
        raise SystemExit(1)
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted([p for p in pdf_dir.glob('**/*') if p.is_file() and p.suffix.lower() == '.pdf'])
    print(f"Found {len(pdf_files)} PDFs in {pdf_dir}")

    converted = 0
    for pdf in pdf_files:
        txt_name = pdf.with_suffix('.txt').name
        txt_path = out_dir / txt_name
        txt = pdf_to_text(pdf)
        with txt_path.open('w', encoding='utf-8') as fh:
            fh.write(txt)
        converted += 1
    print(f"Wrote {converted} text files to {out_dir}")


if __name__ == '__main__':
    main()
