from flask import Flask, request, render_template
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    xml_output = ''
    is_admin = False
    parsed_name = ''

    if request.method == 'POST':
        name = request.form.get('name', '')

        # 🛑 Vulnerable to XML Tag Injection
        xml_output = f"""<?xml version="1.0"?>
<user>
    <name>{name}</name>
</user>
"""

        try:
            root = ET.fromstring(xml_output)
            names = root.findall('name')
            admins = root.findall('admin')

            parsed_name = ', '.join([n.text or '' for n in names])

            for admin in admins:
                if admin.text and admin.text.strip().lower() == 'true':
                    is_admin = True
        except Exception as e:
            parsed_name = f"XML parse error: {str(e)}"

    return render_template('index.html',
                           parsed_name=parsed_name,
                           is_admin=is_admin,
                           xml_output=xml_output)

if __name__ == '__main__':
    app.run(debug=True)
