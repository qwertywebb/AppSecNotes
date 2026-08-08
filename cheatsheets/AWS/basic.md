#  AWS Pentest

## 1. Установка и настройка AWS CLI

```bash
# Установка
pip3 install awscli

# Проверка установки
aws --version

# Создать профиль
aws configure --profile target

# Создать профиль с временными ключами (сессия)
aws configure --profile temp

# Просмотр текущего профиля
aws configure list

# Просмотр всех профилей
aws configure list-profiles
```


## 2. Работа с профилями

```bash
# Использовать конкретный профиль
aws s3 ls --profile target

# Использовать профиль по умолчанию
aws s3 ls

# Переключиться на другой профиль через переменную
export AWS_PROFILE=target
aws s3 ls
```


## 3. Переменные окружения (для временных ключей)

```bash
# Установить ключи для текущей сессии
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
export AWS_DEFAULT_REGION=us-east-1

# Проверить, кто ты
aws sts get-caller-identity

# Очистить переменные
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```


## 4. STS (Security Token Service) — кто я и что могу

```bash
# Кто я
aws sts get-caller-identity --profile target

# Получить временные ключи через AssumeRole
aws sts assume-role --role-arn arn:aws:iam::123456789012:role/MyRole --role-session-name MySession --profile target

# Получить права пользователя (имитация)
aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::123456789012:user/username --action-names "s3:ListBucket" --profile target
```


## 5. S3 (Storage) — самый частый вектор

```bash
# Список всех бакетов
aws s3 ls --profile target

# Список бакетов с деталями (API)
aws s3api list-buckets --profile target

# Содержимое бакета (рекурсивно)
aws s3 ls s3://bucket-name/ --recursive --profile target

# Скачать всё из бакета
aws s3 cp s3://bucket-name/ ./download/ --recursive --profile target

# Загрузить файл в бакет
aws s3 cp shell.php s3://bucket-name/ --profile target

# Удалить всё из бакета
aws s3 rm s3://bucket-name/ --recursive --profile target

# Проверить права бакета
aws s3api get-bucket-acl --bucket bucket-name --profile target
aws s3api get-bucket-policy --bucket bucket-name --profile target

# Список публичных бакетов (с помощью специальных инструментов)
# Используй S3Scanner или CloudBrute
```


## 6. DynamoDB (База данных NoSQL)

```bash
# Список таблиц
aws dynamodb list-tables --profile target --region us-east-1

# Получить все записи из таблицы (скан)
aws dynamodb scan --table-name TableName --region us-east-1 --profile target

# Получить конкретную запись по ключу
aws dynamodb get-item --table-name TableName --key '{"id":{"S":"guest-123"}}' --region us-east-1 --profile target

# Записать данные
aws dynamodb put-item --table-name TableName --item '{"id":{"S":"hacker"},"name":{"S":"test"}}' --profile target

# Удалить запись
aws dynamodb delete-item --table-name TableName --key '{"id":{"S":"guest-123"}}' --profile target

# Описание таблицы (структура)
aws dynamodb describe-table --table-name TableName --profile target
```


## 7. IAM (Identity and Access Management)

```bash
# Кто я
aws sts get-caller-identity --profile target

# Список всех пользователей
aws iam list-users --profile target

# Информация о конкретном пользователе
aws iam get-user --user-name username --profile target

# Политики, прикреплённые к пользователю
aws iam list-attached-user-policies --user-name username --profile target

# Инлайн-политики пользователя
aws iam list-user-policies --user-name username --profile target

# Список всех ролей
aws iam list-roles --profile target

# Политики роли
aws iam list-attached-role-policies --role-name roleName --profile target

# Список групп
aws iam list-groups --profile target

# Политики группы
aws iam list-attached-group-policies --group-name groupName --profile target

# Проверить, есть ли права на действие
aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::123456789012:user/username --action-names "s3:ListBucket" --profile target
```

---

## 8. EC2 (Виртуальные машины)

```bash
# Список всех EC2 инстансов
aws ec2 describe-instances --profile target --region us-east-1

# Список инстансов с IP
aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,PublicIpAddress,PrivateIpAddress]" --output table --profile target

# Получить публичные IP всех инстансов
aws ec2 describe-instances --query "Reservations[*].Instances[*].PublicIpAddress" --output text --profile target

# Список Security Groups
aws ec2 describe-security-groups --profile target --region us-east-1

# Получить метаданные EC2 (если есть доступ к инстансу)
curl http://169.254.169.254/latest/meta-data/
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

---

## 9. Lambda

```bash
# Список всех Lambda функций
aws lambda list-functions --profile target --region us-east-1

# Получить код функции
aws lambda get-function --function-name FunctionName --profile target

# Выполнить функцию
aws lambda invoke --function-name FunctionName --payload '{"key":"value"}' output.txt --profile target

# Политика функции (разрешения)
aws lambda get-policy --function-name FunctionName --profile target
```

---

## 10. Secrets Manager / SSM Parameter Store

```bash
# Список всех секретов
aws secretsmanager list-secrets --profile target --region us-east-1

# Получить секрет
aws secretsmanager get-secret-value --secret-id SecretName --profile target

# Список параметров SSM
aws ssm get-parameters-by-path --path / --recursive --profile target --region us-east-1

# Получить параметр
aws ssm get-parameter --name /path/to/param --with-decryption --profile target
```

---

## 11. RDS (Базы данных)

```bash
# Список RDS инстансов
aws rds describe-db-instances --profile target --region us-east-1

# Список Aurora кластеров
aws rds describe-db-clusters --profile target

# Получить строку подключения
aws rds describe-db-instances --query "DBInstances[*].[DBInstanceIdentifier,Endpoint.Address,Endpoint.Port]" --output table --profile target
```

---

## 12. CloudTrail (Логи)

```bash
# Список трейлов
aws cloudtrail describe-trails --profile target

# Читать логи за последнее время
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin --profile target

# Последние события
aws cloudtrail lookup-events --max-items 50 --profile target
```

---

## 13. SQS / SNS

```bash
# Список очередей SQS
aws sqs list-queues --profile target --region us-east-1

# Получить сообщение из очереди
aws sqs receive-message --queue-url https://sqs.region.amazonaws.com/123456789012/queue-name --profile target

# Список топиков SNS
aws sns list-topics --profile target
```

---

## 14. Cognito (Identity Pools)

```bash
# Список identity pools
aws cognito-identity list-identity-pools --max-results 20 --profile target --region us-east-1

# Получить информацию о пуле
aws cognito-identity describe-identity-pool --identity-pool-id us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --profile target
```

---

## 15. Вспомогательные инструменты

```bash
# Установка Pacu (AWS Pentest Framework)
git clone https://github.com/RhinoSecurityLabs/pacu
cd pacu && bash install.sh
python3 pacu.py

# Установка S3Scanner (поиск открытых бакетов)
pip3 install s3scanner
s3scanner --bucket-list buckets.txt

# CloudBrute (поиск открытых облачных ресурсов)
https://github.com/0xsha/CloudBrute
```


## 📌 Самые частые команды (шпаргалка для пентеста)

| Что нужно | Команда |
| :--- | :--- |
| **Кто я?** | `aws sts get-caller-identity` |
| **Где я?** | `aws configure list` |
| **Какие бакеты?** | `aws s3 ls` |
| **Какие таблицы?** | `aws dynamodb list-tables` |
| **Какие секреты?** | `aws secretsmanager list-secrets` |
| **Какие EC2?** | `aws ec2 describe-instances` |
| **Какие пользователи?** | `aws iam list-users` |
| **Что я могу?** | `aws iam list-attached-user-policies` |
| **Проверить права** | `aws iam simulate-principal-policy` |

---

## 🚀 Быстрый старт (для нового профиля)

```bash
# 1. Настроить профиль
aws configure --profile target

# 2. Проверить себя
aws sts get-caller-identity --profile target

# 3. Разведка
aws s3 ls --profile target
aws dynamodb list-tables --region us-east-1 --profile target
aws iam list-users --profile target

# 4. Если есть бакет
aws s3 ls s3://bucket-name/ --recursive --profile target
aws s3 cp s3://bucket-name/ ./download/ --recursive --profile target

# 5. Если есть таблица
aws dynamodb scan --table-name TableName --region us-east-1 --profile target
```


**Запомнить:** AWS пентест — это всегда про IAM, S3 и DynamoDB. Начинай с этих трёх сервисов. 🚀