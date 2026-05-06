# NUCLEI - инструмент для сканирования уязвимостей на основе шаблонов
# Использует готовые YAML шаблоны для обнаружения CVE, misconfiguration, exposed panels и т.д.
# Быстрый, многопоточный, поддерживает HTTP/DNS/TCP/SSL протоколы

# Базовое сканирование
nuclei -u https://target.com
nuclei -l urls.txt
nuclei -list urls.txt

# Шаблоны
nuclei -u https://target.com -t cves/          # CVE шаблоны
nuclei -u https://target.com -t technologies/   # Технологии
nuclei -u https://target.com -t misconfiguration/
nuclei -u https://target.com -t ~/nuclei-templates/

# Фильтрация
nuclei -u https://target.com -severity critical,high
nuclei -u https://target.com -tags cve,owasp
nuclei -u https://target.com -exclude-tags dos

# Вывод
nuclei -u https://target.com -o results.txt
nuclei -u https://target.com -json -o results.json
nuclei -u https://target.com -silent

# Обновление шаблонов
nuclei -update-templates

# Аутентификация
nuclei -u https://target.com -header "Authorization: Bearer token"
nuclei -u https://target.com -cookie "session=value"

# Скорость
nuclei -u https://target.com -rate-limit 150 -c 25

# Без проверки SSL
nuclei -u https://target.com -no-verify
