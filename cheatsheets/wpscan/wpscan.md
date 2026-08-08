┌─────────────────────────────────────────────────────────────────────────────┐
│                    WPScan - CHEATSHEET (WordPress Security Scanner)         │
├─────────────────────────────────────────────────────────────────────────────┤
│  НАЗНАЧЕНИЕ: Поиск уязвимостей в WordPress (ядра, плагины, темы),           │
│              перечисление пользователей, брутфорс паролей                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  # Базовое сканирование                                                     │
│  wpscan --url http://example.com                                           │
│                                                                             │
│  # Обновление базы уязвимостей                                              │
│  wpscan --update                                                            │
│                                                                             │
│  # Перечисление пользователей                                               │
│  wpscan --url http://example.com --enumerate u                             │
│  wpscan --url http://example.com --enumerate u1-10                         │
│                                                                             │
│  # Перечисление плагинов (требуется API-токен)                              │
│  wpscan --url http://example.com --enumerate vp      # уязвимые            │
│  wpscan --url http://example.com --enumerate ap      # все                 │
│  wpscan --url http://example.com --enumerate ap --detection-mode aggressive│
│                                                                             │
│  # Перечисление тем (требуется API-токен)                                   │
│  wpscan --url http://example.com --enumerate vt      # уязвимые            │
│  wpscan --url http://example.com --enumerate at      # все                 │
│                                                                             │
│  # Перечисление всего сразу                                                 │
│  wpscan --url http://example.com --enumerate u,vp,vt,ap,at                 │
│                                                                             │
│  # Брутфорс паролей                                                         │
│  wpscan --url http://example.com --usernames admin --passwords rockyou.txt │
│  wpscan --url http://example.com --usernames users.txt --passwords rockyou.txt│
│  wpscan --url http://example.com --usernames admin --passwords rockyou.txt \│
│          --password-attack xmlrpc   # атака через xmlrpc (быстрее)         │
│                                                                             │
│  # Сохранение результата                                                    │
│  wpscan --url http://example.com --output scan.txt                         │
│  wpscan --url http://example.com --format json --output scan.json          │
│                                                                             │
│  # Дополнительные опции                                                     │
│  wpscan --url http://example.com --random-user-agent   # обход блокировки  │
│  wpscan --url http://example.com --follow-redirection  # следовать редиректу│
│  wpscan --url http://example.com --request-timeout 30  # таймаут           │
│                                                                             │
│  # API-токЕН (обязателен для поиска уязвимостей плагинов/тем)              │
│  # Получить бесплатно: https://wpvulndb.com/                               │
│  wpscan --url http://example.com --api-token TOKEN --enumerate vp,vt       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘