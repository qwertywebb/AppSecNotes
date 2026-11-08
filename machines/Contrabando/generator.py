import random
import string

def generate_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    random.seed()
    secret = input("Any words you want to add to the password? ")
    password_characters = list(characters + secret)
    random.shuffle(password_characters)
    password = ''.join(password_characters[:length])

    print("Generated password:",password)
    return password

try:
    length = int(raw_input("Enter the desired length of the password: "))
except NameError:
    length = int(input("Enter the desired length of the password: "))
except ValueError:
    print("Invalid input. Using default length of 12.")
    length = 12

password = generate_password(length)
