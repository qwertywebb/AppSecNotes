# MITRE ATT&CK

**MITRE ATT&CK** — это база знаний о поведении реальных атакующих.

Расшифровка:

> **Adversarial Tactics, Techniques, and Common Knowledge**

ATT&CK разработан [MITRE ATT&CK](https://attack.mitre.org/?utm_source=chatgpt.com).

Главное отличие от PTES, OSSTMM и других методологий:

* PTES / OSSTMM - объясняют, КАК проводить пентест

* MITRE ATT&CK - описывает, ЧТО делают атакующие

ATT&CK — **не методология проведения пентеста**, а стандартизированная база знаний и язык для описания действий атакующего.


# Структура ATT&CK

ATT&CK представляет техники в виде **матрицы**.

## 1. Tactics — зачем?

**Tactic** — это цель атакующего, то есть **зачем он выполняет действие**.

Например:

```text
Initial Access
↓
получить первоначальный доступ

Credential Access
↓
получить учётные данные

Discovery
↓
исследовать систему

Lateral Movement
↓
перемещаться по сети
```

У Enterprise ATT&CK есть 14 основных тактик:

```text
Reconnaissance
Resource Development
Initial Access
Execution
Persistence
Privilege Escalation
Defense Evasion
Credential Access
Discovery
Lateral Movement
Collection
Command and Control
Exfiltration
Impact
```


## 2. Techniques — как?

**Technique** — конкретный способ достижения цели.

Например:

```text
Tactic:
Initial Access
       ↓
Technique:
Phishing
T1566
```

То есть:

```text
Зачем? → Initial Access
Как?   → Phishing
ID     → T1566
```

Другой пример:

```text
Tactic:
Initial Access
       ↓
Technique:
Exploit Public-Facing Application
T1190
```


## 3. Sub-techniques — более конкретный способ

Некоторые техники делятся на подкатегории.

Например:

```text
T1566 — Phishing
│
├── T1566.001
│   Spearphishing Attachment
│
├── T1566.002
│   Spearphishing Link
│
└── T1566.003
    Spearphishing via Service
```

То есть структура:

```text
TACTIC
   ↓
TECHNIQUE
   ↓
SUB-TECHNIQUE
```


# Пример

Атакующий отправил сотруднику письмо с вредоносным вложением.

Это можно описать так:

```text
Tactic:
Initial Access

Technique:
Phishing — T1566

Sub-technique:
Spearphishing Attachment — T1566.001
```


# Что содержится в каждой технике

Каждая техника ATT&CK может содержать:

* описание техники;
* ID техники;
* примеры использования реальными threat groups;
* рекомендации по обнаружению;
* mitigations;
* связанные sub-techniques.

Например, если в отчёте указан:

```text
T1566.001
```

команда защиты может найти эту технику в ATT&CK и посмотреть:

```text
Как это делают атакующие?
↓
Как это обнаруживать?
↓
Как защищаться?
```


# ATT&CK и пентест

ATT&CK **не заменяет PTES**.

Правильнее понимать так:

```text
PTES
↓
структурирует процесс пентеста

MITRE ATT&CK
↓
помогает классифицировать действия и техники атакующего
```

Например, во время пентеста:

```text
Phishing
↓
получили Initial Access
↓
украли credentials
↓
переместились на другой сервер
↓
получили данные
```

Это можно сопоставить с ATT&CK:

| Действие                                                            | Tactic            | ATT&CK      |
| ------------------------------------------------------------------- | ----------------- | ----------- |
| Фишинговое письмо с вложением                                       | Initial Access    | `T1566.001` |
| Эксплуатация публичного приложения                                  | Initial Access    | `T1190`     |
| Извлечение credentials из ОС                                        | Credential Access | `T1003`     |
| Использование украденных учётных данных для доступа к другому хосту | Lateral Movement  | `T1550`     |
| Получение данных из базы данных/репозитория                         | Collection        | `T1213`     |


# Зачем это нужно в отчёте

Без ATT&CK:

```text
Найдена уязвимость.
Получен доступ.
Получены credentials.
```

С ATT&CK:

```text
Initial Access
T1190 — Exploit Public-Facing Application

Credential Access
T1003 — OS Credential Dumping

Lateral Movement
T1550 — Use Alternate Authentication Material
```

Таким образом, клиент понимает не только:

> **«Какую уязвимость нужно исправить?»**

но и:

> **«Какие техники реальных атакующих мы сейчас не умеем обнаруживать?»**


# Главное, что нужно запомнить

```text
MITRE ATT&CK
=
база знаний о поведении атакующих
```

```text
Tactic
=
ЗАЧЕМ атакующий выполняет действие
```

```text
Technique
=
КАК он достигает цели
```

```text
Sub-technique
=
конкретный вариант выполнения техники
```

### Самая важная мысль

> **PTES, OSSTMM и другие фреймворки говорят, как проводить пентест. MITRE ATT&CK не описывает процесс пентеста — он предоставляет стандартизированный язык для описания техник и поведения атакующего.**

Именно поэтому ATT&CK хорошо использовать **вместе с пентест-фреймворком**, сопоставляя найденные в ходе тестирования действия и техники с соответствующими ATT&CK ID.
