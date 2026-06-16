MongoDb:

# Вернуть первого пользователя.
user[$ne]=dfdsfdsfdsf&pass[$ne]=dfdsfdsfdsf

# Вернуть первого пользователя из базы не admin, не pedro и пароль не dfdsfdsfdsf
user[$nin][]=admin&user[$nin][]=pedro&pass[$ne]=dfdsfdsfdsf