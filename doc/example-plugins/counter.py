from __future__ import unicode_literals
# don't convert to ascii in py2.7 when creating string to return

import time

outputs = []
crontable = []
crontable.append([2, "say_hello"])

def say_hello():
    outputs.append(["G1FHUFHHU", "hello world"])
