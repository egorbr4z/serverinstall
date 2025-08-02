#!/usr/bin/env python3

import subprocess
import os

os.system("clear")
print("Hello! Chose your system:")
print("Debian = 1 | Arch = 2 | Fedora = 3"
)
system = int(input("Number:"))

if system == 1:
     subprocess.run(["python3", "debian.py"])
if system == 2:
     subprocess.run(["python3", "arch.py"])
if system == 3:
     subprocess.run(["python3", "fedora.py"])
#os.system(f"python start.py && exit")
