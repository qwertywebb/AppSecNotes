# NIST SP 800-115 

**NIST SP 800-115 — Technical Guide to Information Security Testing and Assessment.**

Методология NIST для систематической оценки безопасности информационных систем.

Это **не только пентест**. Она охватывает:

* анализ документации;
* анализ конфигураций;
* анализ логов;
* сканирование уязвимостей;
* валидацию уязвимостей;
* penetration testing.

### 3 основные цели

```text
1. Найти уязвимости
2. Проверить эффективность security controls
3. Проверить, можно ли реально эксплуатировать найденные слабости
```


# 3 фазы

## 1. Planning

До начала тестирования определить:

```text
Scope
Objectives
Rules of Engagement
Communication
Testing windows
Emergency stop conditions
```

Результат → **формальный Test Plan**.


## 2. Execution

Четыре категории техник:

```text
Review Techniques
        ↓
Target Identification & Analysis
        ↓
Target Vulnerability Validation
        ↓
Penetration Testing
```

### Review

Изучение:

* документации;
* политик;
* конфигураций;
* ACL;
* firewall rules.

### Target Identification & Analysis

Определение:

* живых хостов;
* открытых портов;
* сервисов;
* технологий.

### Vulnerability Validation

Проверка, что найденная уязвимость **реальна**, а не ложное срабатывание.

### Penetration Testing

Реальная эксплуатация для определения возможного воздействия.

**Важно:** не каждое исследование обязано доходить до полноценного пентеста.


## 3. Post-Testing

После тестирования:

```text
Analyze
   ↓
Prioritize
   ↓
Report
   ↓
Remediate
```

Нужно:

* определить severity;
* описать влияние;
* указать затронутые security controls;
* дать конкретные рекомендации по исправлению.

Просто:

> «Обнаружена SQL Injection»

— недостаточно.

Нужно указать **где**, **что можно получить** и **как исправить**.


# Главное отличие

**NIST SP 800-115 = широкая методология security assessment, а не исключительно penetration testing.**

Она определяет **подходы и процессы**, а не конкретные инструменты.

### Плюсы

* структурированный подход;
* подходит для разных инфраструктур;
* признан NIST;
* широко применим в government/enterprise;
* обеспечивает повторяемость тестирования.

### Минусы

* это **guidance, а не regulation**;
* не устанавливает обязательную периодичность тестов;
* требует квалифицированных специалистов.

### Для запоминания

```text
NIST SP 800-115

PLAN
  ↓
EXECUTE
  ├─ Review
  ├─ Identify & Analyze
  ├─ Validate Vulnerabilities
  └─ Penetration Test
  ↓
POST-TEST
  ├─ Analyze
  ├─ Prioritize
  ├─ Report
  └─ Remediate
```

**Ключевая мысль:** NIST SP 800-115 помогает не просто «найти уязвимости», а **системно проверить безопасность и доказать, насколько реально эти уязвимости могут быть использованы**.
