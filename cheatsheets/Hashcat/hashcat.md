# Hashcat

## 📖 Что такое Hashcat

Hashcat — это инструмент для взлома паролей с использованием GPU/CPU. Он поддерживает сотни алгоритмов хэширования (MD5, SHA1, bcrypt, NTLM, Kerberos, и т.д.).


## 🧠 Основные понятия

| Термин | Описание |
|--------|----------|
| **Mode (-m)** | Алгоритм хэширования (например, 1000 — NTLM, 3200 — bcrypt) |
| **Attack Mode (-a)** | Тип атаки (0 — словарная, 3 — маска, 6 — гибрид) |
| **Rule (-r)** | Правила мутации пароля (например, `dive.rule`) |
| **Wordlist** | Список паролей (например, `rockyou.txt`) |
| **Hash file** | Файл с хэшами для взлома |


## 🔥 Режимы атак

### 0 — Словарная атака (стандартная)

```bash
hashcat -m 3200 hash.txt /usr/share/wordlists/rockyou.txt
```

### 3 — Маска (брутфорс по шаблону)

```bash
# 8 цифр (от 00000000 до 99999999)
hashcat -m 1000 hash.txt -a 3 ?d?d?d?d?d?d?d?d

# 8 символов: цифры + строчные буквы
hashcat -m 1000 hash.txt -a 3 ?d?l?l?l?l?l?l?l
```

**Символы масок:**
- `?l` — строчные буквы (a-z)
- `?u` — заглавные (A-Z)
- `?d` — цифры (0-9)
- `?s` — спецсимволы (!@#$%^&*)
- `?a` — все (l + u + d + s)

### 6 — Гибрид (словарь + маска)

```bash
# rockyou + 2 цифры в конце
hashcat -m 1000 hash.txt -a 6 rockyou.txt ?d?d
```


## 📋 Правила (Rules)

Правила позволяют **мутировать** пароли из словаря, создавая тысячи вариаций из одного слова. Например, из `password` можно получить `Password1!`, `P@ssw0rd`, `password123`.

### Базовые правила

| Правило | Описание | Пример (password) |
|---------|----------|-------------------|
| `c` | Первая буква заглавная | `Password` |
| `u` | Все буквы заглавные | `PASSWORD` |
| `l` | Все буквы строчные | `password` |
| `s0` | Замена `o` на `0` | `passw0rd` |
| `s@` | Замена `a` на `@` | `p@ssword` |
| `$1` | Добавить `1` в конец | `password1` |
| `$!` | Добавить `!` в конец | `password!` |
| `^P` | Добавить `P` в начало | `Password` |
| `d` | Удвоить слово | `passwordpassword` |
| `r` | Развернуть слово | `drowssap` |
| `[` | Удалить первый символ | `assword` |
| `]` | Удалить последний символ | `passwor` |

### Комбинирование правил (цепочка)

```bash
# password → Password1!
echo "password" | hashcat --stdout -r /usr/share/hashcat/rules/best64.rule
```


## 🚀 Использование правил с `dive.rule`

```bash
echo "spring2026" > base.txt
hashcat --stdout base.txt -r /usr/share/hashcat/rules/dive.rule > wordlist.txt
```

**Что происходит:**
1. `base.txt` содержит одно слово: `spring2026`
2. `dive.rule` — это набор из сотен правил мутации
3. `hashcat --stdout` генерирует все вариации и сохраняет в `wordlist.txt`

**Пример вариаций `spring2026` с `dive.rule`:**
- `Spring2026`
- `SPRING2026`
- `spring2026!`
- `Spring2026!`
- `spring2027`
- `spring2026_`
- `spring2026#`
- ... (сотни вариантов)


## 📁 Популярные файлы правил

| Файл | Описание |
|------|----------|
| `best64.rule` | 64 самых эффективных правила |
| `dive.rule` | ~500 правил, используется для брутфорса |
| `rockyou-30000.rule` | Расширенный набор для `rockyou.txt` |
| `leetspeak.rule` | Замена букв на цифры/символы |

Путь:
```
/usr/share/hashcat/rules/
```


## 🛠️ Полезные команды

### Генерация словаря из одного слова с правилами

```bash
echo "password" | hashcat --stdout -r /usr/share/hashcat/rules/best64.rule > wordlist.txt
```

### Генерация вариаций из списка слов

```bash
hashcat --stdout -r /usr/share/hashcat/rules/dive.rule < base.txt > wordlist.txt
```

### Применение правил к существующему словарю

```bash
hashcat -m 1000 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

### Показать найденный пароль

```bash
hashcat -m 1000 hash.txt --show
```

### Тестирование скорости

```bash
hashcat -b
```


## 🎯 Популярные режимы Hashcat

| Mode | Алгоритм | Пример |
|------|----------|--------|
| `0` | MD5 | `hashcat -m 0 hash.txt rockyou.txt` |
| `1000` | NTLM | `hashcat -m 1000 hash.txt rockyou.txt` |
| `1800` | SHA512 | `hashcat -m 1800 hash.txt rockyou.txt` |
| `3200` | bcrypt | `hashcat -m 3200 hash.txt rockyou.txt` (медленно) |
| `5600` | NetNTLMv2 | `hashcat -m 5600 hash.txt rockyou.txt` |
| `13100` | Kerberos TGS | `hashcat -m 13100 hash.txt rockyou.txt` |
| `18200` | AS-REP | `hashcat -m 18200 hash.txt rockyou.txt` |
| `22000` | WPA/WPA2 | `hashcat -m 22000 hash.txt rockyou.txt` |


## 📌 Шпаргалка (быстрые команды)

```bash
# Взлом NTLM
hashcat -m 1000 hash.txt /usr/share/wordlists/rockyou.txt

# Взлом с правилами
hashcat -m 1000 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Генерация словаря из base.txt с dive.rule
hashcat --stdout base.txt -r /usr/share/hashcat/rules/dive.rule > wordlist.txt

# Брутфорс маской (8 цифр)
hashcat -m 1000 hash.txt -a 3 ?d?d?d?d?d?d?d?d

# Гибрид: словарь + 2 цифры
hashcat -m 1000 hash.txt -a 6 rockyou.txt ?d?d

# Показать результат
hashcat -m 1000 hash.txt --show

# Ускорить bcrypt
hashcat -m 3200 hash.txt rockyou.txt -w 3 --force
```