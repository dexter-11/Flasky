from flask import Flask, render_template, request, send_file, redirect, url_for
import requests
import os
import uuid

app = Flask(__name__)
TEMP_FOLDER = "fetched_pages"
os.makedirs(TEMP_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target_url = request.form.get('url')
        try:
            response = requests.get(target_url, timeout=5)
            filename = f"{uuid.uuid4()}.html"
            filepath = os.path.join(TEMP_FOLDER, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            return redirect(url_for('render_page', filename=filename, url=target_url))
        except Exception as e:
            return render_template('result.html', url=target_url, error=str(e))
    return render_template('index.html')

@app.route('/view/<filename>')
def render_page(filename):
    return render_template('result.html', filename=filename, url=request.args.get("url"))

@app.route('/fetched/<filename>')
def serve_file(filename):
    return send_file(os.path.join(TEMP_FOLDER, filename))

if __name__ == '__main__':
    app.run(debug=True)