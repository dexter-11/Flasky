<?php
  // Simple logger for OOB XXE testing
  $log_file = 'xxe_oob_log.txt';
  
  $entry  = "[" . date("Y-m-d H:i:s") . "] ";
  $entry .= $_SERVER['REMOTE_ADDR'] . " ";
  $entry .= $_SERVER['REQUEST_METHOD'] . " ";
  $entry .= $_SERVER['REQUEST_URI'] . "\n";
  
  file_put_contents($log_file, $entry, FILE_APPEND);
  
  header('Content-Type: text/plain');
  echo "OOB XXE received and logged.";
?>
