# Сергей Гребенщиков

**Penetration Tester (Web / Internal)**

> Из разработки в безопасность: 4 года писал код, последние 1.5 года — ломаю и защищаю.

[![TryHackMe](https://img.shields.io/badge/TryHackMe-150%2B%20machines-brightgreen)](https://tryhackme.com/p/moersvziseropms3)
[![eJPT](https://img.shields.io/badge/eJPT-2026-blue)]()
[![OWASP](https://img.shields.io/badge/OWASP-Top%2010-orange)](https://owasp.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK-red)](https://attack.mitre.org/)

## О себе

- 4 года коммерческой разработки (React, Vue, Next.js, Docker, CI/CD)
- 1.5 года в безопасности приложений: поиск и эксплуатация уязвимостей, secure code review, реагирование на инциденты
- 150+ машин на TryHackMe: веб, Active Directory, повышение привилегий, Windows, Linux
- Читаю код и понимаю, где разработчик допустил ошибку

## Опыт в безопасности

- **Аудит ERP-системы** — выявил SQL-инъекции, IDOR, нарушения авторизации, хранение паролей в открытом виде. Подготовил отчёт, ТЗ на рефакторинг, сопровождал устранение до закрытия всех критичных уязвимостей.
- **Реагирование на инцидент** — восстановил сервис на Next.js после эксплуатации RCE (CVE-2025-55182): изоляция, ротация ключей, восстановление из бэкапа, внедрение WAF.

## Инструменты

**Пентест и разведка**
Kali, Nmap, Masscan, Metasploit, Burp Suite, OWASP ZAP, Wireshark, tcpdump, sqlmap, John the Ripper, Hydra, Hashcat, Gobuster, ffuf, dirsearch, nuclei, Amass, Subfinder, Nikto

**C2**
Empire + Starkiller

**Active Directory и Windows**
Impacket, PowerShell, Mimikatz, BloodHound

**Сети и ОС**
Linux (Ubuntu, Kali), Windows (клиентские и серверные), TCP/IP, HTTP/HTTPS, DNS, ARP, DHCP, VLAN, VPN, Active Directory

**Веб и архитектура**
JavaScript, TypeScript, Python, Bash, REST, GraphQL, WebSocket, JWT, OAuth 2.0, CSP

**Безопасная разработка**
OWASP Top 10, MITRE ATT&CK, параметризованные запросы, bcrypt, WAF на Nginx (rate limiting, блокировка по IP)

**DevOps**
Docker, Git, CI/CD (базово), VirtualBox

## Cheatsheets

Систематизированная база знаний по полному циклу пентеста: от разведки до пост-эксплуатации.

### Reconnaissance & Enumeration
- Active / Passive Recon — `nmap`, `enum4linux`, Google Dork, `searchsploit`
- Directory Fuzzing — `gobuster`, `ffuf`, `nikto`, `dirsearch`
- Subdomain Enumeration — `Amass`, `Subfinder`
- Protocol Analysis — `Wireshark`, `tcpdump`

### Web Application Attacks
- Injections — SQLi, Command Injection, Wildcard Injection
- File Vulnerabilities — LFI, RFI, Insecure Deserialization
- Auth & Tokens — JWT, OAuth, CSRF
- Advanced Web — SSRF, HTTP Request Smuggling, Prototype Pollution
- Client-Side — XSS, Browser Security

### Password Attacks
- Cracking — `John the Ripper`, `hydra`, `medusa`, `Hashcat`
- Hash Analysis — `CyberChef`

### Post-Exploitation & Privilege Escalation
- Linux — команды, повышение привилегий, права
- Windows — внутреннее устройство, службы, повышение привилегий, Active Directory, BloodHound

### Development & Automation
- `Python` — скрипты для автоматизации пентеста
- `reverse_shell` — генерация и обработка реверс-шеллов

### Misc
- `steganography` — CTF
- `zip` — работа с архивами

## Writeups

- **Быстрый writeup** (15 мин) — для закрепления
- **Полный отчёт** (1–2 часа) — для ключевых машин

## Сертификация

- eJPT (2026)
- Готовлюсь к OSCP

## Контакты

- Telegram: [@GrebenshchikovSergey](https://t.me/GrebenshchikovSergey)
- Email: landhardy22@gmail.com
- THM: [tryhackme.com/p/moersvziseropms3](https://tryhackme.com/p/moersvziseropms3)
