# АТАКА: GOLDEN TICKET

## Что это:
Подделка TGT (Ticket Granting Ticket) с использованием хэша учетной записи KRBTGT.

## Почему это работает:
- Все TGT в домене зашифрованы хэшем KRBTGT
- Если атакующий получил этот хэш, он может подделать TGT для ЛЮБОГО пользователя
- Domain Controller не может отличить подделку от настоящего билета

## Что нужно для атаки:
- Хэш KRBTGT
- SID домена
- Имя целевого пользователя (обычно Administrator)

## Где взять хэш KRBTGT:
- Дамп ntds.dit с DC
- DCSync атака (Mimikatz: lsadump::dcsync /user:krbtgt)
- Дамп памяти lsass на DC

## Инструменты:
- Mimikatz (kerberos::golden)
- Impacket (ticketer.py)

## Пример с Impacket:
ticketer.py -nthash <KRBTGT_хэш> -domain-sid <SID_домена> -domain thm.loc Administrator

SID домена можно получить:
- lookupsid.py домен/пользователь@IP
- Из любого объекта домена (первые части SID)

## Пример с Mimikatz:
kerberos::golden /user:Administrator /domain:thm.loc /sid:<SID_домена> /krbtgt:<хэш> /ticket:golden.kirbi

## Использование билета:
export KRB5CCNAME=Administrator.ccache
smbclient.py thm.loc/Administrator@SERVER1.thm.loc -k -no-pass

## Что дает Golden Ticket:
- Полный контроль над всем доменом
- Доступ к любым ресурсам
- Права Domain Admin

## Ограничения:
- Работает ТОЛЬКО в рамках одного домена
- Для леса целиком нужен Enterprise Golden Ticket (хэш KRBTGT из корневого домена)

## Защита:
- Регулярно менять пароль KRBTGT (минимум 2 раза для очистки истории т.к предыдущий тоже кэшируется)
- Использовать Managed Service Accounts для служб
- Ограничить использование NTLM
- Мониторинг аномалий в Kerberos трафике (инструменты Rubeus)