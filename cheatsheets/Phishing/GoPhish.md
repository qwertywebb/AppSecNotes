## ⚙️ GoPhish — основные команды и шаги

1. Установка и запуск:

```bash
wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip
unzip gophish-v0.12.1-linux-64bit.zip
sudo ./gophish
```

2. Доступ к веб-панели: `https://127.0.0.1:3333`
3. Настройки:
   - **Sending Profiles**: SMTP-сервер для рассылки.
   - **Email Templates**: шаблоны писем (HTML / текст).
   - **Landing Pages**: фейковые страницы сбора логинов.
   - **Users & Groups**: список жертв (email, доп. параметры).
   - **Campaigns**: запуск кампании с привязкой шаблона, группы, лендинга.

## 📊 Аналитика в GoPhish

- Отправлено, доставлено, открыто, кликнуто, введены данные.
- География (IP-адреса и User-Agent жертв).
- Даты и время.