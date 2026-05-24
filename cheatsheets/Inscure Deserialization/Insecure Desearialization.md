# Суть уязвимости
# Принимают от пользователя сериализованные данные и передают в unserialize() → Можно подменить объект → автоматически вызовутся магические методы (__wakeup, __destruct) → RCE / SQLi / обход авторизации.

---НАПРИМЕР---

O:7:"Example":1:{s:4:"data";s:10:"exploit";}
При десериализации PHP создаст объект класса Example и вызовет его магические методы.

---------------------

🔍 Белый ящик (есть код)
# Ищи функции:

PHP: serialize(), unserialize()

Python: pickle.loads(), pickle.dumps()

Java: readObject(), writeObject(), ObjectInputStream

.NET: BinaryFormatter, SoapFormatter, JavaScriptSerializer

Ruby: Marshal.load(), Marshal.dump()

Node.js: node-serialize, serialize-to-js

🖤 Черный ящик (нет кода)
1. Куки
Base64 строки в куках — декодируй, ищи O: (PHP объекты)

Сессии PHP: могут хранить сериализованные данные

2. Ошибки
Фразы: unserialize(), Object deserialization error, ClassNotFoundException

3. ViewState ASP.NET
Поле __VIEWSTATE — декодируй Base64, смотри структуру

4. Трюк с тильдой ~
Добавляй ~ к именам PHP файлов (file.php~) — ищи бэкапы редакторов

Могут сохраниться исходники с функциями сериализации

5. JSON
Подозрительные JSON-структуры в запросах/ответах