from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        target_url = request.form.get('url')
        try:
            response = requests.get(target_url, timeout=5)
            content = response.text
        except Exception as e:
            content = f"Error fetching URL: {str(e)}"
        return render_template('result.html', url=target_url, content=content)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)