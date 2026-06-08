# BLOODHOUND — ГРАФОВЫЙ АНАЛИЗ ACTIVE DIRECTORY

## Что это

BloodHound — инструмент, который превращает перечисление AD в граф.
Вместо плоских списков пользователей и групп показывает СВЯЗИ между ними.

Ключевая фраза:
"Defenders think in lists. Attackers think in graphs."

## Архитектура BloodHound

1. Сборщик данных (SharpHound / bloodhound-python)
2. База данных (Neo4j)
3. Веб-интерфейс для анализа

---

# ЭТАП 1: СБОР ДАННЫХ (COLLECTORS)

## SharpHound (Windows, C#)

SharpHound.exe --CollectionMethods All --Domain tryhackme.loc --ExcludeDCs

Параметры:
--CollectionMethods All — все методы сбора
--Domain — целевой домен
--ExcludeDCs — исключить DC (тише, безопаснее)

## BloodHound.py (Linux, Python)

bloodhound-python -u username -p password -d DOMAIN -ns DNS_SERVER -c All --zip

Параметры:
-u, -p — учетные данные
-d — домен
-ns — DNS сервер (обычно DC)
-c All — все методы сбора
--zip — упаковать результат в ZIP

## Результат сбора

Файл: YYYYMMDDHHMMSS_bloodhound.zip (или .json)
Содержит: пользователи, группы, компьютеры, ACL, сессии, доверия

## Stealth советы (не попасться)

--ExcludeDCs — не трогать DC
DCOnly — только минимальные запросы к DC
Запуск с non-domain-joined машины через runas /netonly


# ЭТАП 2: ЗАГРУЗКА ДАННЫХ В BLOODHOUND

## Доступ к BloodHound-CE (веб)

http://IP:8080

## Импорт ZIP файла

Administration → File Ingest → Upload ZIP


# ЭТАП 3: АНАЛИЗ В BLOODHOUND

## Основные элементы

Node (узел) — пользователь, группа, компьютер, OU, GPO
Edge (связь) — отношение между узлами (MemberOf, AdminTo, CanRDP и др.)

## Поиск узла

В строке поиска ввести имя (например, ASREPUSER1)

## Информация об узле (правая панель)

- Object information — имя, тип, домен, SID
- Sessions — активные сессии
- Member of — группы, в которых состоит
- Local admin privileges — где есть права админа
- Execution privileges — RDP, WinRM, PSRemote
- Outbound object control — какие права у этого объекта над другими
- Inbound object control — какие права у других над этим объектом

## Built-in queries (готовые запросы)

Cypher → папка → выбор запроса

Полезные запросы:
- "All Domain Admins" — все админы домена
- "Find Shortest Paths to Domain Admins" — путь к админам
- "Find Computers with Unsupported OS" — устаревшие ОС

## Pathfinding (поиск пути)

Pathfinding → Start Node (например, EMPANADAL0V3R) → End Node (Tier 1 ADMINS) → Run

BloodHound покажет ВСЕ пути атаки от пользователя до цели.

## Типы связей (edges) которые важно знать

MemberOf — прямое членство в группе
AdminTo — локальный администратор на компьютере
HasSession — пользователь имеет сессию на компьютере
CanRDP — может подключиться по RDP
CanPSRemote — может подключиться по WinRM
GenericAll — полный контроль над объектом
WriteDacl — может изменять ACL
AllowedToAct — может делегировать
AddMember — может добавить пользователя в группу
ForceChangePassword — может сменить пароль


# ПОЧЕМУ BLOODHOUND ТАК МОЩНЫЙ

Без BloodHound: ты видишь списки пользователей и групп, но не видишь связи.
С BloodHound: ты видишь, что пользователь имеет сессию на компьютере, где админ залогинен → можно украсть токен.

## Пример пути

Пользователь имеет AdminTo на ComputerA
ComputerA имеет HasSession от Domain Admin
→ Пользователь может стать Domain Admin через кражу токена

BloodHound показывает такие пути за секунды.


# ОГРАНИЧЕНИЯ

- SharpHound шумный (может быть замечен)
- Требует учетных данных для сбора
- Нет данных о всех сессиях (только те, которые удалось собрать)
- Не показывает все возможные атаки (только известные)


# БЫСТРАЯ ШПАРГАЛКА

# Сбор данных (Linux)
bloodhound-python -u user -p pass -d DOMAIN -ns DC_IP -c All --zip

# Сбор данных (Windows)
SharpHound.exe --CollectionMethods All --Domain DOMAIN --ExcludeDCs

# Поиск пути в BloodHound
Pathfinding → Start Node → End Node → Run

# Полезные запросы
"Find Shortest Paths to Domain Admins"
"Find Computers where User has Local Admin Rights"
"Find All Sessions"
"Find Unsigned Computers"

# Ключевые edges для поиска
MemberOf, AdminTo, HasSession, CanRDP, GenericAll