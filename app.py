from flask import Flask, request, render_template, send_file
from form_responses import form_answers
from celery import Celery
from subprocess import Popen
import os

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'  # Redis server
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

llm_analyses_dir = './llm_analyses'

def safe_filename(s):
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in s)

@celery.task
def run_adherence_analysis():
    adherence_process = Popen(["python", "adherence_analysis.py"])
    adherence_process.wait()
    print(f"Adherence analysis for completed.")

@celery.task
def run_framework_analysis():
    framework_process = Popen(["python", "framework_analysis.py"])
    framework_process.wait()
    print(f"Framework analysis for completed.")

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    form_text = []
    for i in range(1,16):
        form_text.append(request.form.get(f'step{i}-text'))
    filename = safe_filename(form_answers[0])

    return render_template('submit_success.html', filename = filename)

@app.route('/download-report/<filename>')
def download_report(filename):
    run_adherence_analysis.apply_async()
    adherence_output_filepath = os.path.join(f'{llm_analyses_dir}/{filename}', "adherence-analysis.txt")
    if os.path.exists(adherence_output_filepath):
        return send_file(adherence_output_filepath, as_attachment=True)
    else:
        return render_template('file_404.html'), 404

@app.route('/chat/<filename>')
def chat(filename):
    run_framework_analysis.apply_async()
    framework_output_filepath = os.path.join(f'{llm_analyses_dir}/{filename}', "framework-analysis.txt")
    if os.path.exists(framework_output_filepath):
        return send_file(framework_output_filepath, as_attachment=True)
    else:
        return render_template('file_404.html'), 404
    # return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True)
