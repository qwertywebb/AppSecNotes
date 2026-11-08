<?php
    $path = '/etc/passwd';
    $SECRET_KEY='an8h6oTlNB9N0HNcJMPYJWypPR2786IQ4I3woPA1BqoJ7hzIS0qQWi2EKmJvAgOW';
    $computed_hash=hash_hmac('sha256', $path, $SECRET_KEY);
    echo $computed_hash
?>
