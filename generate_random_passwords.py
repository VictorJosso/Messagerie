import random

def generate(lenth):
    pwd = ""
    for x in range(int(lenth)):
        pwd+=chr(random.randint(33,122))
    return pwd
