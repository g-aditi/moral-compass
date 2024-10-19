from flask import Flask, request, render_template
from form_responses import get_form_inputs

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
    return "Form submitted successfully!"

if __name__ == '__main__':
    app.run(debug=True)
