# Отчёт по исследованию CryptoCabana

## 1. Краткое резюме

В рамках лабораторной работы была исследована инфраструктура CryptoCabana, построенная на базе Microsoft Azure.

Основная цепочка атаки выглядела следующим образом:

```text
Web application
      │
      ▼
Azure Static Website
      │
      ▼
Исходный JavaScript
      │
      ▼
Azure Blob Storage
      │
      ▼
SAS Token
      │
      ▼
Перечень контейнеров Storage Account
      │
      ▼
Контейнер vault
      │
      ▼
backup-service-account.json
      │
      ▼
Service Principal credentials
      │
      ▼
Azure CLI authentication
      │
      ▼
Azure Key Vault
      │
      ▼
Secret enumeration
      │
      ▼
key-shard-1
key-shard-2
key-shard-3
      │
      ▼
Версионирование key-shard-2
      │
      ▼
Старое значение секрета
      │
      ▼
Сборка флага
```

Главная идея лаборатории заключается не в эксплуатации классической серверной уязвимости, а в **цепочке ошибок конфигурации и управления секретами в Azure**:

1. клиентскому JavaScript был выдан SAS-токен с избыточными возможностями;
2. с помощью SAS удалось перечислить контейнеры Storage Account;
3. был обнаружен контейнер `vault`, который не должен был быть доступен атакующему;
4. в контейнере находился JSON с credentials Service Principal;
5. полученные credentials позволили аутентифицироваться в Azure;
6. Service Principal имел права на чтение секретов Azure Key Vault;
7. один из секретов был ротирован, однако старая версия осталась доступной;
8. старая версия содержала недостающий фрагмент флага.

---

# 2. Что такое Azure с точки зрения Red Team

Перед разбором атаки важно понять базовую модель Azure.

Если упростить Azure до нескольких основных понятий:

```text
Microsoft Entra ID
       │
       │ отвечает за личности
       ▼
Users / Service Principals
       │
       │ получают права
       ▼
Subscription
       │
       ▼
Resource Groups
       │
       ├── Storage Account
       │      ├── $web
       │      ├── backups
       │      └── vault
       │
       └── Key Vault
              ├── secret
              ├── secret
              └── secret
```

Для Red Team важно разделять **Identity Plane** и **Resource/Data Plane**.

### Identity Plane

Здесь находятся:

* пользователи;
* Service Principals;
* Managed Identities;
* Microsoft Entra ID;
* tenants;
* роли и права.

### Resource/Data Plane

Здесь находятся непосредственно данные:

* Blob Storage;
* Key Vault;
* databases;
* virtual machines;
* App Services;
* Storage Accounts и т.д.

Это важное различие.

Например:

```text
az resource list
```

работает с Azure Resource Manager.

А запрос:

```text
https://account.blob.core.windows.net/container/file
```

идёт непосредственно к **data plane Blob Storage**.

Поэтому вполне возможно получить доступ к данным через SAS, даже если команда:

```text
az storage account list
```

ничего не показывает.

---

# 3. Что такое Tenant

В лаборатории использовался Microsoft Entra tenant.

Упрощённо:

```text
Tenant = отдельная среда идентификации Azure
```

В лаборатории tenant имел домен:

```text
thmctf.onmicrosoft.com
```

и соответствующий Tenant ID.

Внутри tenant находятся:

```text
Users
Service Principals
Applications
Groups
Roles
```

Tenant отвечает прежде всего за **кто ты**.

---

# 4. Что такое Subscription

Subscription — это область, в которой находятся Azure-ресурсы и к которой применяются разрешения, биллинг и управление ресурсами.

В лаборатории использовалась subscription:

```text
Az-Subs-CTF
```

То есть логика примерно такая:

```text
Tenant
  │
  └── Subscription
         │
         ├── Resource Group
         │      ├── Storage Account
         │      └── Key Vault
         │
         └── другие ресурсы
```

---

# 5. Почему дали Azure Portal и Cloud Shell

На первом этапе лаборатории выдали пользовательские credentials.

После открытия Azure Portal, выбрав Bash Cloud Shell и выполнив:

```bash
az account show
```

Ответ:

```json
{
  "name": "Az-Subs-CTF",
  "subscription": "...",
  "tenantId": "...",
  "user": {
    "name": "usr-08086788@thmctf.onmicrosoft.com",
    "type": "user"
  }
}
```

Это означало:

```text
Ты
 │
 └── authenticated user
          │
          ▼
      Entra ID
          │
          ▼
      Tenant
          │
          ▼
     Subscription
```

То есть Cloud Shell уже был авторизован от имени лабораторного пользователя.

---

# 6. Почему без этого доступа сайт всё равно открывался

Сам сайт:

```text
https://cryptocabanaf5scjagc.z13.web.core.windows.net/
```

является публичным Static Website.

Поэтому:

```text
Browser
   │
   ▼
Static Website
```

не требует твоей Azure-аутентификации.

Однако Azure credentials были нужны **для дальнейшей работы с Azure API и ресурсами**, когда лаборатория предоставляла соответствующие права.

Именно поэтому здесь существовали две разные вещи:

```text
Доступ к веб-сайту
        ≠
Доступ к Azure subscription
```

Это очень важное различие для Red Team.

---

# 7. Что такое Storage Account

Далее обнаружено:

const url =
    "https://" + STORAGE_ACCOUNT + ".blob.core.windows.net/" +
    BACKUPS_CONTAINER + "/" + blobName + "?" + BACKUP_SAS;


```text
cryptocabanaf5scjagc.blob.core.windows.net
```

Это Azure Storage Account.

Storage Account можно представить как большой контейнер хранения данных.

Внутри него находятся контейнеры:

```text
Storage Account
│
├── $web
├── backups
└── vault
```

Каждый контейнер содержит Blob-объекты.

Например:

```text
vault/
    backup-service-account.json
    seed_phrase.txt
```

---

# 8. Что такое Blob

Blob — это объект хранения.

Очень грубо можно представить его как файл:

```text
container/file
```

Например:

```text
vault/seed_phrase.txt
```

получается по адресу:

```text
https://cryptocabanaf5scjagc.blob.core.windows.net/vault/seed_phrase.txt?SAS
```

Azure Blob Storage предоставляет REST API для работы с такими объектами.

Например, перечисление Blob внутри контейнера выполняется через:

```text
GET /container?restype=container&comp=list
```

Microsoft прямо документирует этот механизм для Blob Storage.

---

# 9. Что такое `$web`

Контейнер:

```text
$web
```

имеет специальное назначение.

Он используется Azure Static Website для хранения файлов сайта:

```text
index.html
style.css
script.js
images/
...
```

Поэтому когда ты открываешь:

```text
https://cryptocabanaf5scjagc.z13.web.core.windows.net/
```

ты фактически обращаешься к содержимому `$web`.

То есть:

```text
Web browser
      │
      ▼
Static Website
      │
      ▼
Storage Account
      │
      ▼
$web container
```

---

# 10. Анализ JavaScript

На странице был обнаружен JavaScript:

```javascript
const STORAGE_ACCOUNT = "cryptocabanaf5scjagc";
const BACKUPS_CONTAINER = "backups";
const BACKUP_SAS = "?sv=...";
```

Это очень важная находка.

Особенно:

```javascript
BACKUP_SAS
```

SAS означает:

**Shared Access Signature.**

Это специальный подписанный токен, который позволяет получить ограниченный доступ к ресурсам Azure Storage без полноценной Azure-аутентификации.

---

# 11. Почему SAS очень важен для Red Team

Представь:

```text
Azure Storage
      │
      └── обычно требует authorization
```

Но приложение может дать пользователю:

```text
SAS token
```

и сказать:

```text
"Вот URL, по которому ты можешь работать с этим Blob."
```

SAS содержит ограничения:

```text
sv  = API version
ss  = services
srt = resource types
sp  = permissions
st  = start time
se  = expiration
spr = protocol
sig = signature
```

В этом случае особенно важным было:

```text
sp=rl
```

то есть:

```text
r = read
l = list
```

Для Account SAS Microsoft документирует, что permission `l` позволяет выполнять операции перечисления, а `r` — чтение.

---

# 12. Почему SAS оказался интереснее самого сайта

В JavaScript был URL вида:

```text
https://cryptocabanaf5scjagc.blob.core.windows.net/...
```

с SAS-параметрами.

Вместо того чтобы ограничиться тем, что делает интерфейс, фокус исследования был на самом Azure Storage API.

Это правильный Red Team подход:

```text
UI
 │
 ├── что показывает?
 │
 └── какие backend/storage/API
     используются на самом деле?
```

Очень часто frontend скрывает больше, чем кажется.

---

# 13. Почему CORS сначала мешал

При попытке выполнить:

```text
PUT
```

браузер сначала отправил:

```text
OPTIONS
```

Это был CORS preflight:

```http
OPTIONS /backups/backup-....txt
Origin: https://cryptocabanaf5scjagc...
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: x-ms-blob-type
```

Azure ответил:

```text
403 CORS not enabled or no matching rule found
```

Это не означало:

```text
SAS invalid
```

Это означало:

```text
Browser → Azure Blob
          │
          └── CORS policy rejected request
```

Azure Blob Storage действительно использует `OPTIONS` preflight для проверки CORS rules. Если подходящего правила нет, Storage отвечает `403`.

---

# 14. Очень важное различие: CORS ≠ Authorization

Это один из главных уроков лаборатории.

CORS:

```text
Можно ли браузеру отправить/прочитать cross-origin request?
```

Authorization:

```text
Имеет ли клиент право выполнить операцию?
```

Это совершенно разные вещи.

Например:

```text
curl
```

не является браузером и не обязан соблюдать браузерную same-origin policy.

Поэтому возможно сделать:

```bash
curl ...
```

и напрямую общаться с Blob Storage.

Microsoft отдельно подчёркивает, что CORS не является механизмом авторизации.

---

# 15. Проверка контейнера backups

После корректного использования SAS:

```bash
curl -i "https://cryptocabanaf5scjagc.blob.core.windows.net/backups?restype=container&comp=list&SAS"
```
Получено:
```xml
<?xml version="1.0" encoding="utf-8"?><EnumerationResults ServiceEndpoint="https://cryptocabanaf5scjagc.blob.core.windows.net/" ContainerName="backups"><Blobs /><NextMarker /></EnumerationResults>%
```

Это означало:

```text
SAS работает
        │
        ▼
можно обращаться к Blob Storage
        │
        ▼
можно выполнять list/read операции
```

---

# 16. Проверка записи

Таккже была попытка записи:

```bash
curl -i -X PUT \
  -H "x-ms-blob-type: BlockBlob" \
  --data 'test' \
  "https://cryptocabanaf5scjagc.blob.core.windows.net/backups/test.txt?SAS

и получено:

```text
403 AuthorizationPermissionMismatch
```

Это очень полезный результат.

Почему?

Потому что он подтвердил:

```text
SAS разрешает:
    READ
    LIST

SAS НЕ разрешает:
    WRITE
```

То есть:

```text
sp=rl
```

не давал возможность изменить Blob.

Это хороший пример того, почему всегда нужно анализировать **реальные permissions**, а не предполагать их.

---

# 17. Перечисление контейнеров Storage Account

После этого был выполнен запрос:

```text
GET https://cryptocabanaf5scjagc.blob.core.windows.net/?comp=list&SAS
```

Ответ:

```text
$web
backups
vault
```

Это был переломный момент.

До этого приложение показывало только:

```text
backups
```

Но Storage Account фактически содержал:

```text
$web
backups
vault
```

То есть доверие к данным frontend позволило обнаружить ресурс, на который сама веб-страница явно не ссылалась.

Azure Blob Storage предоставляет отдельную операцию List Containers для перечисления контейнеров Storage Account.

---

# 18. Почему `vault` оказался особенно интересным

Название:

```text
vault
```

сразу является сильным индикатором.

Для Red Team:

```text
backup
config
secret
private
internal
vault
keys
credentials
```

— это имена, которые требуют особого внимания.

После обнаружения контейнера:

```text
vault
```

следующим шагом было:

```text
List Blobs
```

для этого контейнера.

C помощью запроса:
```bash
https://cryptocabanaf5scjagc.blob.core.windows.net/vault?restype=container&SAS
```

Получен список:

```text
backup-service-account.json
seed_phrase.txt
```

---

# 19. Получение seed phrase

Был выполнен запрос:

```bash
curl -s "https://cryptocabanaf5scjagc.blob.core.windows.net/vault/seed_phrase.txt?SAS"

```

и получена секретная фраза.

Однако сама seed phrase не была конечной целью.

Это соответствует формулировке задания:

> Somewhere in there is a second, more valuable set of keys.

То есть лаборатория специально заставляла продолжать исследование.

---

# 20. Самая важная находка — backup-service-account.json

Затем был получен:

```text
vault/backup-service-account.json
```

С помощью запроса:
```bash
curl -s "https://cryptocabanaf5scjagc.blob.core.windows.net/vault/seed_phrase.txt?SAS"
```

Внутри находились:

```json
{
    "client_id": "...",
    "client_secret": "...",
    "key_vault_name": "ccabana-kv-f5scjagc",
    "key_vault_uri": "https://ccabana-kv-f5scjagc.vault.azure.net/",
    "tenant_id": "..."
}
```

Это критическая находка.

Здесь впервые появляется полноценная Azure identity:

```text
client_id
client_secret
tenant_id
```

---

# 21. Что такое Service Principal

Service Principal — это не обычный пользователь.

Упрощённо:

```text
Human:
    username + password

Application:
    Service Principal
       │
       ├── client/application ID
       └── credential
```

Service Principal используется приложениями, автоматизацией, CI/CD и сервисами для аутентификации в Azure.

Microsoft описывает Service Principal как identity, не привязанную к конкретному пользователю, которой можно назначать Azure permissions.

---

# 22. Что означали найденные поля

### `client_id`

Идентификатор приложения / Service Principal.

Можно представить:

```text
"Кто ты?"
        ↓
client_id
```

### `client_secret`

Секрет, доказывающий владение этой identity.

```text
"Докажи, что ты действительно этот Service Principal"
        ↓
client_secret
```

### `tenant_id`

Говорит Azure:

```text
"В каком Entra tenant находится эта identity?"
```

---

# 23. Авторизация service-principal

Использован:

```bash
az login --service-principal \      
  --username \
  --password  \
  --tenant 
```

и получен ответ:
```text
[
  {
    "cloudName": "AzureCloud",
    "homeTenantId": "tenant_id",
    "id": "2492269a-2948-46fd-aae3-68c9b066443a",
    "isDefault": true,
    "managedByTenants": [],
    "name": "Az-Subs-CTF",
    "state": "Enabled",
    "tenantId": "8f8c5f8e-42d3-4ceb-97ad-241bbf446d6c",
    "user": {
      "name": "dbcf2923-e4eb-4b72-a0a4-688aa1185cf5",
      "type": "servicePrincipal"
    }
  }
]


```

После этого локальная авторизация через Azure CLI успешно сработала.

Команда, которая была использована, является штатным способом входа Service Principal через client secret. Microsoft документирует именно такую форму `az login --service-principal --username ... --password ... --tenant ...`.

---

# 24. Почему после входа `az account show` показал Service Principal

После успешного входа:

```bash
az account show
```

показал:

```json
"user": {
    "name": "...",
    "type": "servicePrincipal"
}
```

Это важный момент.

До этого:

```text
user.type = user
```

После компрометации credentials:

```text
user.type = servicePrincipal
```

То есть произошло переключение:

```text
Human identity
      │
      ▼
Service Principal identity
```

Это классическая модель cloud privilege escalation / identity abuse.

---

# 25. Почему `az resource list` сначала был пустым

До использования Service Principal выполнено:

```bash
az resource list
az storage account list
```

и получен пустой результат.

Это не противоречие.

Есть два разных способа доступа:

```text
Management Plane
        │
        └── Azure Resource Manager
                │
                └── az resource list
```

и:

```text
Data Plane
        │
        └── Blob Storage
                │
                └── SAS
```

SAS предоставлял определённые операции непосредственно над Storage data plane.

А Azure CLI под исходным пользователем не имел нужных management permissions.

---

# 26. Что такое Key Vault

Следующий найденный ресурс:

```text
ccabana-kv-f5scjagc
```

— Azure Key Vault.

Key Vault предназначен для хранения:

```text
secrets
keys
certificates
```

В лаборатории именно здесь находились части флага.

Упрощённая схема:

```text
Storage Account
      │
      └── backup-service-account.json
                 │
                 ▼
          Service Principal
                 │
                 ▼
            Key Vault
                 │
                 ├── key-shard-1
                 ├── key-shard-2
                 ├── key-shard-3
                 └── master-key
```

---

# 27. Почему `az keyvault show` не сработал

Изначально:

```bash
az keyvault show \
    --name ccabana-kv-f5scjagc
```

вернул:

```text
Vault not found within subscription
```

Но затем:

```bash
az keyvault secret list \
    --vault-name ccabana-kv-f5scjagc
```

вернул:

```text
ForbiddenByRbac
```

и особенно интересное:

```text
Resource:
.../resourceGroups/cryptocabana-rg/providers/Microsoft.KeyVault/vaults/...
```

Это уже доказало, что Key Vault существует.

Проблема была не в отсутствии ресурса, а в разрешениях на конкретную операцию.

---

# 28. RBAC

RBAC означает:

**Role-Based Access Control.**

Упрощённо:

```text
Identity
   │
   ▼
Role
   │
   ▼
Permission
   │
   ▼
Resource
```

Например:

```text
Service Principal
       │
       ▼
Key Vault Secrets User
       │
       ▼
читать secrets
       │
       ▼
Key Vault
```

В данном случае после аутентификации Service Principal получил достаточные права на чтение секретов Key Vault.

---

# 29. Почему это важный Red Team урок

Получение:

```text
client_secret
```

не означает автоматически:

```text
root Azure
```

Нужно всегда делать:

```text
Credentials
   │
   ▼
Authenticate
   │
   ▼
Who am I?
   │
   ▼
What can I access?
   │
   ▼
What resources?
   │
   ▼
What data?
```

То есть после получения cloud credentials всегда следует выполнять **permission enumeration**.

---

# 30. Перечисление секретов

После успешной аутентификации:

```bash
az keyvault secret list \
    --vault-name ccabana-kv-f5scjagc \
    -o table
```

получен список:

```text
key-shard-1
key-shard-2
key-shard-3
master-key
```

Само наличие:

```text
master-key
```

уже является сильным индикатором.

Но лаборатория специально подготовила более интересный путь через `key-shard-2`.

---

# 31. Получение первого фрагмента

Команда:

```bash
az keyvault secret show \
    --vault-name ccabana-kv-f5scjagc \
    --name key-shard-1 \
    --query value \
    -o tsv
```

вернула:

```text
THM{n0t_ur
```

Получаем:

```text
THM{n0t_ur...
```

---

# 32. Получение третьего фрагмента

Аналогично:

```bash
az keyvault secret show \
    --vault-name ccabana-kv-f5scjagc \
    --name key-shard-3 \
    --query value \
    -o tsv
```

вернуло:

```text
ur_c01ns!}
```

Теперь:

```text
THM{n0t_ur
          ???
ur_c01ns!}
```

Осталась середина.

---

# 33. Что было необычного в key-shard-2

Текущий `key-shard-2` вернул не фрагмент флага, а сообщение:

```text
Rotated this after IT flagged it --
old value should still be recoverable if you know where to look.
```

Это практически прямой hint на:

```text
Secret Versioning
```

---

# 34. Что такое version у Key Vault Secret

Очень важная концепция Azure Key Vault:

Secret имеет не просто:

```text
name
value
```

а концептуально:

```text
name
 ├── version A
 │      └── old value
 │
 └── version B
        └── current value
```

Когда secret обновляется, Azure создаёт новую версию.

Старая версия не обязательно исчезает.

Microsoft Azure CLI предоставляет специальную команду:

```bash
az keyvault secret list-versions
```

для перечисления версий конкретного secret.

---

# 35. Ошибка с `--version "1"`

Сначала:

```bash
--version "1"
```

Но это не сработало.

Причина проста:

```text
version ≠ номер 1
```

Azure использует уникальный идентификатор версии, например:

```text
3d6492d2c6f74123bc754a9ded22b2a0
```

Поэтому правильный процесс:

```bash
az keyvault secret list-versions \
    --vault-name ccabana-kv-f5scjagc \
    --name key-shard-2
```

Затем найти:

```text
version ID
```

и передать именно его:

```bash
az keyvault secret show \
    --vault-name ccabana-kv-f5scjagc \
    --name key-shard-2 \
    --version "<VERSION_ID>" \
    --query value \
    -o tsv
```

Azure CLI официально описывает `list-versions` как команду для получения всех версий конкретного secret.

---

# 36. Получение старого значения

Получена старая версия:

```text
_k3ys_n0t_
```

Теперь вся конструкция стала очевидной:

```text
key-shard-1
THM{n0t_ur

key-shard-2 OLD VERSION
_k3ys_n0t_

key-shard-3
ur_c01ns!}
```

Соединяем:

```text
THM{n0t_ur
+
_k3ys_n0t_
+
ur_c01ns!}
```

Получаем:

```text
THM{n0t_ur_k3ys_n0t_ur_c01ns!}
```

---

# 37. Полная цепочка атаки

Если смотреть на лабораторию глазами Red Team:

```text
[1] Public web application
             │
             ▼
[2] JavaScript disclosure
             │
             ▼
[3] Storage Account identified
             │
             ▼
[4] SAS token discovered
             │
             ▼
[5] SAS permissions: read + list
             │
             ▼
[6] List containers
             │
             ▼
       $web / backups / vault
                         │
                         ▼
[7] List vault blobs
                         │
                         ├── seed_phrase.txt
                         │
                         └── backup-service-account.json
                                      │
                                      ▼
[8] Service Principal credentials
                                      │
                                      ▼
[9] Azure CLI authentication
                                      │
                                      ▼
[10] Enumerate Key Vault
                                      │
                                      ▼
[11] key-shard-1 / 2 / 3
                                      │
                                      ▼
[12] key-shard-2 current value = hint
                                      │
                                      ▼
[13] Enumerate secret versions
                                      │
                                      ▼
[14] Recover old key-shard-2
                                      │
                                      ▼
[15] Assemble flag
```

---

# 38. Что именно было уязвимо

Важно не назвать это одной магической "Azure vulnerability".

Это была **цепочка ошибок конфигурации и управления секретами**.

Основные проблемы:

### 38.1. Избыточно выданный SAS

Frontend содержал SAS, позволяющий:

```text
read
list
```

Причём токен позволял исследовать структуру Storage Account шире, чем требовалось для нормальной работы пользовательского интерфейса.

---

### 38.2. Sensitive data exposure

В доступном контейнере находился:

```text
backup-service-account.json
```

который содержал:

```text
client_id
client_secret
tenant_id
```

То есть credentials были размещены внутри Blob Storage и доступны через SAS.

---

### 38.3. Secret material в Storage

Также в Storage находилась:

```text
seed_phrase.txt
```

Хранение чувствительных секретов в доступном Blob-контейнере является плохой практикой.

---

### 38.4. Избыточные права Service Principal

Полученные credentials позволили получить доступ к Azure Key Vault.

Следовательно, Service Principal обладал правами, которые позволяли ему читать секреты, необходимые для прохождения лаборатории.

В production среде это должно быть строго ограничено принципом:

```text
Least Privilege
```

---

### 38.5. Старая версия секрета оставалась доступной

После ротации:

```text
key-shard-2
```

старое значение осталось доступным.

В данном CTF это было сделано намеренно, но в реальной инфраструктуре доступ к старым версиям должен контролироваться в соответствии с политикой хранения и жизненным циклом секретов.

---

# 39. Как должен был выглядеть безопасный дизайн

Безопасная архитектура:

```text
Browser
   │
   ▼
Static Website
   │
   │ только необходимые public assets
   ▼
Backend API
   │
   ▼
Managed Identity
   │
   ▼
Azure Storage
```

А не:

```text
Browser
   │
   ▼
SAS
   │
   ▼
Storage Account
   │
   ├── backups
   ├── vault
   └── credentials
```

---

# 40. Как правильно хранить credentials

Никогда не следует делать:

```text
Storage Blob
   │
   └── client_secret
```

Лучше:

```text
Azure Key Vault
      │
      └── secret
```

А приложение получает секрет через:

```text
Managed Identity
```

или строго ограниченный Service Principal.

---

# 41. Как ограничить SAS

Если приложению необходимо записывать backup:

не следует выдавать:

```text
account-wide
read + list
```

если достаточно:

```text
write
```

к конкретному контейнеру или даже конкретному Blob.

Главный принцип:

```text
Минимальные permissions
+
Минимальный scope
+
Минимальный срок жизни
```

То есть:

```text
не:
Storage Account → read/list

а:
конкретный ресурс → конкретная операция → короткое время
```

---

# 42. Как защитить Blob Storage

Необходимо:

* минимизировать права SAS;
* ограничивать срок действия SAS;
* ограничивать scope;
* не хранить credentials в Blob;
* не хранить seed phrases в Storage без необходимости;
* использовать Private Endpoints там, где это требуется;
* контролировать доступ к Storage через Azure RBAC;
* включать мониторинг Storage;
* регулярно ротировать SAS и credentials.

---

# 43. Как защитить Service Principal

Для Service Principal необходимо:

```text
Least Privilege
```

Например, если автоматизации необходимо читать один конкретный secret:

```text
Service Principal
       │
       ▼
только нужный Key Vault
       │
       ▼
только необходимые secrets
```

а не:

```text
Service Principal
       │
       ▼
весь Azure subscription
```

Также следует:

* использовать managed identities, где возможно;
* минимизировать client secrets;
* использовать короткоживущие credentials;
* контролировать expiration;
* регулярно ротировать secrets;
* мониторить использование Service Principal.

---

# 44. Как защитить Key Vault

Необходимо:

* использовать Azure RBAC;
* минимизировать роли;
* не давать приложению доступ ко всем secrets без необходимости;
* контролировать версии secrets;
* удалять/деактивировать старые версии, когда это допустимо политикой;
* включать logging и monitoring;
* использовать защиту от accidental deletion;
* контролировать доступ к vault на уровне identity и network.

---

# 45. Что должен делать Red Team после получения Azure credentials

Это особенно важно запомнить.

Получил:

```text
client_id
client_secret
tenant_id
```

Не надо сразу пытаться "ломать Azure".

Правильный workflow:

```text
1. Authenticate
        ↓
2. Identify current principal
        ↓
3. Identify tenant
        ↓
4. Identify subscription
        ↓
5. Enumerate accessible resources
        ↓
6. Enumerate RBAC permissions
        ↓
7. Enumerate data-plane permissions
        ↓
8. Search for secrets/configuration
        ↓
9. Identify privilege escalation paths
```

---

# 46. Минимальный набор Azure-команд, который стоит запомнить

### Кто я?

```bash
az account show
```

### Какие subscriptions доступны?

```bash
az account list -o table
```

### Какие ресурсы доступны?

```bash
az resource list -o table
```

### Какие Storage Accounts?

```bash
az storage account list -o table
```

### Key Vault

```bash
az keyvault list -o table
```

### Секреты Key Vault

```bash
az keyvault secret list \
    --vault-name <vault>
```

### Получить secret

```bash
az keyvault secret show \
    --vault-name <vault> \
    --name <secret>
```

### Посмотреть версии

```bash
az keyvault secret list-versions \
    --vault-name <vault> \
    --name <secret>
```

### Получить конкретную версию

```bash
az keyvault secret show \
    --vault-name <vault> \
    --name <secret> \
    --version <VERSION_ID>
```

---

# 47. Что особенно важно запомнить из этой лаборатории

## №1 — Azure CLI и Azure Storage URL могут быть разными уровнями

```text
az resource list
```

не означает:

```text
"я вижу абсолютно всё, что существует в Azure"
```

Нужно различать:

```text
Management Plane
Data Plane
```

---

## №2 — SAS это credential

SAS нельзя воспринимать как "просто часть URL".

Фактически:

```text
?sv=...&sp=...&sig=...
```

является временным authorization mechanism.

Если SAS утёк:

```text
SAS leaked
     ↓
storage access leaked
```

---

## №3 — CORS не защищает Storage

Если браузер говорит:

```text
CORS error
```

это не значит:

```text
ресурс недоступен
```

Это может означать только:

```text
browser запрещает cross-origin request
```

Поэтому при авторизованном тестировании:

```text
Browser
```

и

```text
curl
```

могут давать совершенно разные результаты.

---

## №4 — Имена ресурсов очень важны

В лаборатории:

```text
vault
backup-service-account.json
seed_phrase.txt
key-shard-1
key-shard-2
key-shard-3
master-key
```

всё практически подсказывало направление атаки.

В Red Team всегда нужно обращать внимание на:

```text
backup
old
config
secret
vault
key
credential
internal
private
admin
```

---

## №5 — Rotation не всегда означает уничтожение старого значения

Это был главный урок второй половины лаборатории.

Найден:

```text
current secret
```

и получен:

```text
Rotated...
old value should still be recoverable
```

Следующая мысль должна быть:

```text
Key Vault
    ↓
Secret
    ↓
Versions
```

---

# 48. Что происходило с точки зрения атакующего

Если убрать весь Azure-specific жаргон, ситуация была очень простой.

Компания дала веб-приложению возможность работать с Storage:

```text
"Вот тебе SAS."
```

Но SAS позволил узнать:

```text
"Какие ещё контейнеры существуют?"
```

Обнаружен:

```text
vault
```

В нём лежало:

```text
"Вот credentials другого Azure identity."
```

Использованы эти credentials:

```text
"Теперь я Service Principal."
```

Service Principal имел доступ:

```text
"Вот тебе Key Vault."
```

В Key Vault:

```text
"Вот три части ключа."
```

Но одна часть была заменена:

```text
"Старое значение всё ещё существует."
```

Получен список версий:

```text
secret versions
```

и восстановлено старое значение.

После этого:

```text
THM{n0t_ur
+
_k3ys_n0t_
+
ur_c01ns!}
```

и получил:

```text
THM{n0t_ur_k3ys_n0t_ur_c01ns!}
```

---

# 49. Итоговая оценка с позиции Red Team

Лаборатория демонстрирует типичную для cloud security цепочку:

```text
Information Disclosure
        ↓
Exposed SAS
        ↓
Storage Enumeration
        ↓
Sensitive File Exposure
        ↓
Credential Exposure
        ↓
Service Principal Compromise
        ↓
Cloud Resource Access
        ↓
Key Vault Access
        ↓
Secret Version Enumeration
        ↓
Sensitive Data Recovery
```

Ключевой вывод:

> В облаке компрометация редко выглядит как классический `RCE → root`.

Гораздо чаще цепочка выглядит так:

```text
одна identity
      ↓
получает доступ к ресурсу
      ↓
ресурс раскрывает следующую identity
      ↓
следующая identity имеет больше прав
      ↓
она раскрывает следующий ресурс
      ↓
...
```

Именно поэтому для Red Team специалиста при работе с Azure особенно важно научиться мыслить не только категориями:

```text
Web → RCE → PrivEsc
```

но и:

```text
Identity → Permission → Resource → Secret → Identity → Permission
```

Это и есть одна из основных моделей мышления при cloud penetration testing.

### Полезная официальная документация

[Azure CLI — вход через Service Principal](https://learn.microsoft.com/en-ie/cli/azure/authenticate-azure-cli-service-principal?view=azure-cli-latest)

[Azure CLI — управление Key Vault secrets и версиями](https://learn.microsoft.com/en-us/cli/azure/keyvault/secret?view=azure-cli-latest)

[Azure Blob Storage — List Blobs REST API](https://learn.microsoft.com/en-us/rest/api/storageservices/list-blobs)

[Azure Blob Storage — CORS и preflight requests](https://learn.microsoft.com/en-us/rest/api/storageservices/cross-origin-resource-sharing--cors--support-for-the-azure-storage-services)

[Azure Storage — List Containers REST API](https://learn.microsoft.com/fr-fr/rest/api/storageservices/list-containers2)
