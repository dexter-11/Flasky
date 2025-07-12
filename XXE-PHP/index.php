<?php
function parse_and_authenticate($xmlData) {
    libxml_use_internal_errors(true);

    $dom = new DOMDocument();
    $success = $dom->loadXML($xmlData, LIBXML_NOENT | LIBXML_DTDLOAD); // ⚠ Vulnerable to XXE

    if (!$success) {
        return false;
    }

    $username = $dom->getElementsByTagName('username')->item(0)->nodeValue ?? '';
    $password = $dom->getElementsByTagName('password')->item(0)->nodeValue ?? '';

    // Fake auth check: only admin/admin123 is valid
    return ($username === 'admin' && $password === 'admin123');
}

// ✅ Handle raw XML POST with proper content-type
if ($_SERVER['REQUEST_METHOD'] === 'POST' &&
    strpos($_SERVER['CONTENT_TYPE'], 'application/xml') !== false) {

    $xml = file_get_contents("php://input");
    $auth_success = parse_and_authenticate($xml);

    // Send only a login status div (no reflection of username/password)
    echo "<div class='alert " . ($auth_success ? "alert-success" : "alert-danger") . "'>";
    echo $auth_success ? "✅ Login successful." : "❌ Login failed.";
    echo "</div>";
    exit;
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Products - XXE Lab</title>
    <link href="static/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <h2>🔥 Custom XXE Lab - Flasky</h2>
        <br>
        <h3>🛍 1. PHP Products (Normal Reflected XXE)</h3>
        <div class="list-group mb-5">
            <button class="list-group-item list-group-item-action" onclick="sendXML('100')">Television</button>
            <button class="list-group-item list-group-item-action" onclick="sendXML('101')">Refrigerator</button>
            <button class="list-group-item list-group-item-action" onclick="sendCustomXXE()">🔥 Send XXE Payload</button>
        </div>

        <br/><br/><br/>
        <!-- 🔐 Blind Login via XML -->
        <h3>🛂 2. Login Form (Blind XXE for OOB Attacks)</h3>
        <form id="loginForm">
            <div class="mb-3">
                <input name="username" id="username" class="form-control" placeholder="Username" required>
            </div>
            <div class="mb-3">
                <input name="password" id="password" class="form-control" type="password" placeholder="Password" required>
            </div>
            <button class="btn btn-primary" type="submit">Login</button>
        </form>

        <div id="loginStatus" class="mt-4"></div>
    </div>

    <script src="script.js"></script>
    <script>
        document.getElementById("loginForm").addEventListener("submit", function(e) {
            e.preventDefault();

            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            const xml = `
<?xml version="1.0"?>
<credentials>
    <username>${username}</username>
    <password>${password}</password>
</credentials>
            `.trim();

            fetch("index.php", {
                method: "POST",
                headers: {
                    "Content-Type": "application/xml"
                },
                body: xml
            })
            .then(response => response.text())
            .then(html => {
                document.getElementById("loginStatus").innerHTML = html;
            });
        });
    </script>
</body>
</html>
