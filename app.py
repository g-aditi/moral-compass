from flask import Flask, request, render_template, jsonify, send_file, abort
from form_responses import get_form_inputs
import os
from typing import Optional

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    form_text = []
    for i in range(1,16):
        form_text.append(request.form.get(f'step{i}-text'))

    result = get_form_inputs(form_text)
    return render_template('submit_success.html')


def _latest_analysis_file() -> Optional[str]:
    d = os.path.join(os.getcwd(), 'llm_analyses')
    if not os.path.isdir(d):
        return None
    # Prefer PDF if available (same base name as text analysis), else fall back to text
    pdfs = [os.path.join(d, f) for f in os.listdir(d) if f.endswith('-llm-analysis.pdf')]
    if pdfs:
        latest_pdf = max(pdfs, key=os.path.getmtime)
        return latest_pdf
    texts = [os.path.join(d, f) for f in os.listdir(d) if f.endswith('-llm-analysis.txt')]
    if not texts:
        return None
    latest = max(texts, key=os.path.getmtime)
    return latest


@app.route('/reports/status')
def reports_status():
    """Return JSON with whether a report is available and its URL (if ready)."""
    latest = _latest_analysis_file()
    if latest:
        return jsonify({"ready": True, "url": "/reports/latest"})
    return jsonify({"ready": False})


@app.route('/reports/latest')
def reports_latest():
    latest = _latest_analysis_file()
    if not latest:
        abort(404)
    # If the latest is a PDF, serve it as an attachment so browsers download it.
    if latest.lower().endswith('.pdf'):
        return send_file(latest, mimetype='application/pdf', as_attachment=True, download_name=os.path.basename(latest))
    # otherwise serve plain text
    return send_file(latest, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
