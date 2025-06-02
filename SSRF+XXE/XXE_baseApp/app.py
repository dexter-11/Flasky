from flask import Flask, render_template, request
from lxml import etree

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/product-detail', methods=['POST'])
def product_detail():
    xml_data = request.data or request.form.get('xml')

    try:
        parser = etree.XMLParser(resolve_entities=True)
        root = etree.fromstring(xml_data.encode(), parser=parser)

        product = root.find('.//product')
        name = product.findtext('name')
        code = product.findtext('code')
        tags = product.findtext('tags')
        description = product.findtext('description')

        return render_template('detail.html', name=name, code=code, tags=tags, description=description)
    except Exception as e:
        return f"<h3>Parsing error:</h3><pre>{str(e)}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
