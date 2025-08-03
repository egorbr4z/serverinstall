#!/usr/bin/env python3

import subprocess

print("Sucsess installation!")
print(
"1 - install Let's Encrypt secrificate"
"2 - exit"
)
answer = input(">>>")
if answer == 1:
     subprocess.run(["python3", "sertificate.py"])
else:
     print("Exit...")      
