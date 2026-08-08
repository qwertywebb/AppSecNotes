[!] PENTESTER CHEATSHEET: OAUTH 2.0 (RFC 6749)
[!] Цель: Найти дыры в реализации (redirect_uri, csrf, token leakage)
[!] Фокус: Authorization Code Grant (самый популярный, самые жирные баги)


1. REDIRECT_URI — ГЛАВНАЯ БОЛЬ
   ----------------------------
   Суть: Сервер должен вернуть код на строго указанный URI.
   Если валидация кривая — мы ловим код.

   ЧТО ПРОБОВАТЬ:
   -> Базовый подмен: /?redirect_uri=https://evil.com
   -> Open Redirect внутри домена: /?redirect_uri=https://legit.com/redirect?url=https://evil.com [citation:2][citation:8]
   -> Subdomain Takeover: /?redirect_uri=https://oldsite.legit.com (если поддомен мертвый, регистрируем и ловим токены) [citation:8]
   -> Path Traversal: /?redirect_uri=https://legit.com/callback/../../../evil.com [citation:8]
   -> Fragment в URI: /?redirect_uri=https://legit.com/callback# (токен уйдет во фрагмент, JS может прочитать) [citation:3][citation:8]
   -> Обход валидации через открытый редиректор (например, /logout?continue=attacker.com) [citation:2]
   -> Разные схемы: http:// (если сайт требует https — бан, но если разрешены оба — профит) [citation:5]

   ЕСЛИ РЕДИРЕКТ ЗАБЛОКИРОВАН:
   -> Пробуй обмануть валидацию: 
        *.legit.com  -> xss.legit.com (если есть XSS на поддомене — лутаем код) [citation:3]
        exact match? ищи открытый редирект на этом же домене в другом месте.

2. STATE — ЗАЩИТА ОТ CSRF (ИЛИ ЕЕ ОТСУТСТВИЕ)
   --------------------------------------------
   Если STATE нету или он предсказуемый — мы можем привязать свой акк к жертве.

   АТАКА:
   1. Логинимся через OAuth, ловим Authorization Code (останавливаем запрос).
   2. Создаем страницу с iframe, который шлет этот код на callback жертве.
   3. Если state не проверяется — код залинкуется на аккаунт жертвы. [citation:2]

   ЧТО ЧЕКАТЬ:
   -> Отсутствие параметра state в запросе.
   -> Статичный state (например, "123" или "test").
   -> Предсказуемый state (инкремент, timestamp, слабая рандомизация). [citation:7]
   -> Не проверяется при возврате (можно подставить любой).

3. CSRF + ACCOUNT TAKEOVER (BABY STEP)
   -------------------------------------
   Механика: Жертва авторизована на сайте. Мы заставляем ее браузер выполнить OAuth flow с нашим акком.
   Результат: Наш аккаунт привязывается к жертве — мы заходим через него.

   ВАЖНО: Это работает, если привязка аккаунта (Connect) не требует подтверждения паролем, а просто берет код. [citation:2]

4. TOKEN LEAKAGE ГДЕ ПОПАЛО
   -------------------------
   -> Referer Header: Если сайт редиректит на внешний ресурс после логина, токен может уйти в Referer.
   -> Логи: Иногда токены пишут в логи (уроды).
   -> Browser History: Если токен был в URL (Implicit Flow — RIP), он останется в истории браузера. [citation:10]
   -> http:// (без S) — сниффинг в публичных сетях.

5. PKCE — ЗАЩИТА ОТ ПЕРЕХВАТА (НО НЕ ВСЕГДА)
   -------------------------------------------
   PKCE (Proof Key for Code Exchange) — добавляет code_verifier и code_challenge.
   Если PKCE нет, и мы можем перехватить код (через редирект выше) — мы можем обменять его на токен. [citation:5]
   Если PKCE есть — даже с кодом мы ничего не сделаем без верификатора.

   ЧЕКАТЬ: Есть ли параметры code_challenge в запросе авторизации.

6. TOKEN VALIDATION НА РЕСУРСЕ (API)
   -----------------------------------
   Даже если мы спиздили токен, API может его не принять, если валидирует:
   -> aud (audience) — должен быть тот API, который мы долбим. [citation:5]
   -> iss (issuer) — должен быть правильный сервер.
   -> exp — если токен вечный — это подарок.
   -> sub — если привязка к пользователю.
   -> scope — если узкие права, может быть недопустим для нашего эндпоинта. [citation:6]

   ПРОВЕРЯТЬ: Можно ли использовать токен от одного API для другого? (aud не проверяется) [citation:5]

7. STORAGE (ГДЕ ЛЕЖАТ ТОКЕНЫ)
   ---------------------------
   -> localStorage / sessionStorage — XSS и токены ушли. [citation:5]
   -> HttpOnly Cookie — хорошо, но если не Secure — сниффинг.
   -> Android: keystore? или просто в SharedPreferences? [citation:5]
   -> iOS: Keychain? или плитка?

8. SCOPES (ПРАВА ДОСТУПА)
   ------------------------
   -> Запрашивает ли клиент лишние скоупы? (например, доступ к почте, когда нужен только логин) [citation:5]
   -> Можно ли расширить права? (если нет подписи запроса)
   -> Что произойдет, если скоуп слишком широкий? (PII leakage) [citation:6]

AUTHORIZATION ENDPOINT (клиент -> сервер):
   GET /authorize?
      response_type=code
      client_id=...
      redirect_uri=...   <- СЮДА СМОТРИМ
      scope=...
      state=...          <- СЮДА ТОЖЕ
      code_challenge=... (S256) <- если есть PKCE

TOKEN ENDPOINT (клиент -> сервер):
   POST /token
      grant_type=authorization_code
      code=...
      redirect_uri=...
      client_id=...
      code_verifier=...  <- если есть PKCE
   (здесь можно попробовать replay кода, если нет PKCE)

1. MANUAL:
   -> Burp: Repeater, Intruder (fuzz redirect_uri)
   -> Изменяем redirect_uri на свой коллбек.
   -> Ждем, пока жертва кликнет (или отправляем ссылку).
   -> Profit: код у нас.

2. AUTOMATED:
   -> Используй готовые сканеры ( nuclei с templates на oauth).
   -> Тулзы типа oauth-fuzzer.

3. CHECKLIST SHORT:
   [ ] Можно ли изменить redirect_uri на чужой домен?
   [ ] Есть ли открытый редирект на том же домене, куда можно завернуть?
   [ ] Есть ли параметр state? Он рандомный?
   [ ] Есть ли PKCE (code_challenge)?
   [ ] Работает ли код дважды? (replay)
   [ ] Токены в URL? (Implicit flow — deprecated, но бывает)
   [ ] Куда сохраняются токены на клиенте? (localStorage = instant XSS vector)
   [ ] Валидируется ли audience (aud) на API?
   [ ] Можно ли расширить scope?

-> redirect_uri = святая святых. Любая неточность валидации = Account Takeover. [citation:2]
-> state = must be random and checked. Без него — CSRF и привязка чужого акка. [citation:7]
-> PKCE = must have для публичных клиентов. Без него — код можно обменять, если перехватили. [citation:5]
-> Токены = хранить в HttpOnly, не в localStorage. XSS — и все пропало. [citation:5]
-> Scope = минимально необходимые права. Иначе PII leakage. [citation:6]

[!] Always check: Что будет, если authorization code использовать дважды?
[!] Always check: Что будет, если вставить свой code в чужой flow (если нет state)?
[!] Always check: Поддерживается ли обмен кода через POST с redirect_uri, отличным от исходного?