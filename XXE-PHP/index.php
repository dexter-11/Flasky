<!DOCTYPE html>
<html>
<head>
    <title>Products - XXE Lab</title>
    <link href="static/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <h2>🛍 PHP Products (XXE Test)</h2>
        <div class="list-group">
            <button class="list-group-item list-group-item-action" onclick="sendXML('100')">Television</button>
            <button class="list-group-item list-group-item-action" onclick="sendXML('101')">Refrigerator</button>
            <button class="list-group-item list-group-item-action" onclick="sendCustomXXE()">🔥 Send XXE Payload</button>
        </div>
    </div>

    <script src="script.js"></script>
</body>
</html>
