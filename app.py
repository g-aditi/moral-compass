from flask import Flask, request, render_template, send_file
from form_responses import form_answers
import os

def safe_filename(s):
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in s)

app = Flask(__name__)
llm_analyses_dir = './llm_analyses'

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    form_text = []
    for i in range(1,16):
        form_text.append(request.form.get(f'step{i}-text'))

    from adherence_analysis import filename 
    print(filename)

    return render_template('submit_success.html', filename = filename)

@app.route('/download-report/<filename>')
def download_report(filename):
    adherence_output_filepath = os.path.join(f'{llm_analyses_dir}/{filename}', "adherence-analysis.txt")
    if os.path.exists(adherence_output_filepath):
        return send_file(adherence_output_filepath, as_attachment=True)
    else:
        return "File not found", 404

@app.route('/chat')
def chat():
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True)
