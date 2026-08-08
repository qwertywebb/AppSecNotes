# Чтобы проверить, является ли хост частью AD
systeminfo | findstr Domain

# Получить все активные AD аккаунты(powershell), если часть AD
Get-ADUser  -Filter *