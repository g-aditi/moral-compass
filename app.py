from flask import Flask, request, render_template, jsonify, send_file, abort
from form_responses import get_form_inputs
import os
import json
from typing import Optional

app = Flask(__name__)

# Global variable to track generation progress
generation_progress = {
    "total_questions": 0,
    "completed_questions": 0,
    "current_question": 0,
    "questions_content": [],  # List of completed question analyses
    "is_complete": False,
    "report_path": None
}

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    form_text = []
    for i in range(1,16):
        form_text.append(request.form.get(f'step{i}-text'))

    # Reset progress file before starting new generation
    progress_file = os.path.join(os.getcwd(), 'llm_analyses', 'generation_progress.json')
    os.makedirs(os.path.dirname(progress_file), exist_ok=True)
    with open(progress_file, 'w') as f:
        json.dump({
            "total_questions": 0,
            "completed_questions": 0,
            "current_question": 0,
            "questions_content": [],
            "is_complete": False,
            "report_path": None
        }, f)

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
        # Check if completion marker exists
        completion_marker = latest + '.complete'
        if os.path.exists(completion_marker):
            return jsonify({"ready": True, "url": "/reports/latest"})
        else:
            return jsonify({"ready": False, "message": "Report is still being generated"})
    return jsonify({"ready": False})


@app.route('/reports/progress')
def reports_progress():
    """Return JSON with current generation progress and any new content."""
    global generation_progress

    # Read from progress file if it exists
    progress_file = os.path.join(os.getcwd(), 'llm_analyses', 'generation_progress.json')
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                generation_progress = json.load(f)
        except:
            pass

    return jsonify(generation_progress)


@app.route('/reports/latest')
def reports_latest():
    latest = _latest_analysis_file()
    if not latest:
        abort(404)

    # Check if download parameter is present
    download = request.args.get('download', '0') == '1'

    # If the latest is a PDF, serve it as an attachment so browsers download it.
    if latest.lower().endswith('.pdf'):
        return send_file(latest, mimetype='application/pdf', as_attachment=True, download_name=os.path.basename(latest))

    # For text files, check if user wants to download
    if download:
        return send_file(latest, mimetype='text/plain', as_attachment=True, download_name=os.path.basename(latest))
    else:
        # otherwise serve plain text for viewing in browser
        return send_file(latest, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
