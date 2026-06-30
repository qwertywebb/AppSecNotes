# CREDENTIAL DISCOVERY — ПОИСК ПАРОЛЕЙ В ОТКРЫТЫХ СЕРВИСАХ

## Почему это работает

Разработчики и администраторы часто оставляют пароли там, где не надо:
- В коде (закоммиченные секреты)
- В логах сборки (CI/CD)
- В конфигах на сетевых шарах
- Во внутренних вики

Даже если пароль удалили из текущей версии, он остается в истории коммитов.

## Где искать

### Git репозитории

Что искать:
- История коммитов (git log -p)
- Файлы: .env, web.config, appsettings.json, config.php
- CI/CD файлы: Jenkinsfile, .gitlab-ci.yml
- Хардкод пароли в коде

Ручной поиск:
git log -p | grep -i "password\|secret\|token\|key\|credential"

Автоматизированный поиск (TruffleHog):
trufflehog git file:///path/to/repo

### Jenkins (CI/CD)

Что искать:
- Build console output (логи сборки) — часто печатают env переменные с паролями
- Job конфигурации (config.xml)
- Workspace файлы

Доступ:
- Часто admin:admin или вообще без пароля

API запрос к логам:
curl http://ci.thm.loc/job/JOB_NAME/lastBuild/consoleText | grep -i "password\|secret"

### Другие источники

- Внутренние вики и документация
- Файлы на SMB шарах (web.config, bootstrap.ini, unattend.xml)
- Анонимный LDAP (можно выгрузить пользователей)
- SNMP community strings

## Важно

Не останавливайся на первом найденном пароле. Собирай все:
- Пары username:password
- Только username (потом пригодится для password spraying)
- Паттерны паролей (чтобы угадывать другие)

# TruffleHog — поиск секретов в Git

Отличается от grep тем, что:
- Ищет по ключевым словам (grep умеет)
- Ищет по энтропии (случайности строки) — найдет пароль даже без контекста
- Проверяет всю историю коммитов
- Поддерживает много форматов (JSON, ключи, токены)

Установка:
sudo snap install trufflehog

Запуск на локальном репозитории:
trufflehog git file:///path/to/repo