## OSSTMM

**Главная идея:**

> **OSSTMM = измеряем безопасность, а не высказываем мнение.**

### 🎯 5 каналов — **H-P-W-T-D**

| Канал       | Что проверяем                                |
| ----------- | -------------------------------------------- |
| **HUMSEC**  | 👤 Люди — social engineering                 |
| **PHYSSEC** | 🚪 Физика — двери, доступ, tailgating        |
| **SPECSEC** | 📡 Wireless — Wi-Fi, Bluetooth, RFID         |
| **COMSEC**  | ☎️ Telecom — телефония, VoIP, fax            |
| **DATASEC** | 🌐 Data Networks — сети, сервисы, приложения |

### 🔄 4 фазы — **I-I-I-I**

Запомни как:

> **Найди → Проверь → Взломай → Воздействуй**

1. **Induction** → 🔎 **Enumeration**
   Что существует? Найти и подтвердить assets.

2. **Interaction** → 📏 **Measurement**
   Что реально доступно? Измерить exposure/controls.

3. **Inquiry** → 💥 **Exploitation**
   Можно ли превратить exposure в unauthorized access?

4. **Intervention** → 🛡️ **Response/Audit**
   Исправление, аудит, проверка защит и detection.

### 📊 RAV

**RAV = Risk Assessment Value**

Главная идея:

> **Attack Surface − Controls → Residual Risk**

* **Высокий RAV** → exposure больше, чем эффективно защищено.
* **≈ 0** → controls хорошо соответствуют exposure.

### 📄 Результат

**STAR = Security Test Audit Report**

Это стандартизированный отчёт OSSTMM.

### 🧠 Формула для собеседования

> **OSSTMM = 5 каналов + 4 фазы + измеримые RAV + STAR**

**Если на интервью спросят "чем OSSTMM отличается от обычного pentest?"**:

> **OSSTMM делает акцент не на субъективной оценке риска, а на воспроизводимых измерениях attack surface и эффективности controls.**
