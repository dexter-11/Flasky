from flask import Flask, request, render_template
from lxml import etree

app = Flask(__name__)
XML_DB = 'users.xml'

@app.route('/', methods=['GET', 'POST'])
def index():
    msg = ''
    is_admin = False

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        tree = etree.parse(XML_DB)

        # 🚨 VULNERABLE to XPath Injection
        xpath_query = f"//user[username='{username}' and password='{password}']"

        try:
            result = tree.xpath(xpath_query)

            if result:
                role = result[0].findtext('role')
                if role == 'admin':
                    is_admin = True
                msg = f"✅ Welcome, {username}! Role: {role}"
            else:
                msg = "❌ Invalid credentials"
        except Exception as e:
            msg = f"⚠️ XPath error: {e}"

    return render_template('index.html', msg=msg, is_admin=is_admin)

if __name__ == '__main__':
    app.run(debug=True)
