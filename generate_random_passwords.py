# -*- coding: utf-8 -*-

"""Code par Victor Josso"""

import random

def generate(lenth):
    pwd = ""
    for x in range(int(lenth)):
        rang = random.randint(33, 122)
        if not rang == 92:
            pwd+=chr(rang)
        else:
            pass
    return pwd
