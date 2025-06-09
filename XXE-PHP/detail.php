<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    libxml_disable_entity_loader(false); // VULNERABLE to XXE
    libxml_use_internal_errors(true);

    $xmlData = file_get_contents("php://input");

    $dom = new DOMDocument();
    $parsed = $dom->loadXML($xmlData, LIBXML_NOENT | LIBXML_DTDLOAD); // XXE triggered here

    if (!$parsed) {
        echo "<h3>Error parsing XML</h3>";
        foreach (libxml_get_errors() as $error) {
            echo "<pre>" . htmlspecialchars($error->message) . "</pre>";
        }
        exit;
    }

    $name = $dom->getElementsByTagName('name')->item(0)->nodeValue ?? 'N/A';
    $code = $dom->getElementsByTagName('code')->item(0)->nodeValue ?? 'N/A';
    $tags = $dom->getElementsByTagName('tags')->item(0)->nodeValue ?? 'N/A';
    $desc = $dom->getElementsByTagName('description')->item(0)->nodeValue ?? 'N/A';
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Product Detail</title>
    <link href="static/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <h3>📦 Product Details (Parsed from XML)</h3>
        <ul class="list-group">
            <li class="list-group-item"><strong>Name:</strong> <?= htmlspecialchars($name) ?></li>
            <li class="list-group-item"><strong>Code:</strong> <?= htmlspecialchars($code) ?></li>
            <li class="list-group-item"><strong>Tags:</strong> <?= htmlspecialchars($tags) ?></li>
            <li class="list-group-item"><strong>Description:</strong><br><?= htmlspecialchars($desc) ?></li>
        </ul>
        <a href="index.php" class="btn btn-secondary mt-4">← Back</a>
    </div>
</body>
</html>
