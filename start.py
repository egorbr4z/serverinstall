#!/usr/bin/env python3

import os
import subprocess

# Detect Linux distribution
if os.path.exists('/etc/debian_version'):
    distro = 'debian'
elif os.path.exists('/etc/arch-release'):
    distro = 'arch'
elif os.path.exists('/etc/fedora-release'):
    distro = 'fedora'
else:
    distro = 'unknown'

# Show detection result
os.system("clear")
print(f"Your system: {distro.capitalize()}")
input("Press Enter to continue...")

# Launch appropriate installer
if distro == 'debian':
    subprocess.run(['python3', 'debian.py'])
elif distro == 'arch':
    subprocess.run(['python3', 'arch.py'])
elif distro == 'fedora':
    subprocess.run(['python3', 'fedora.py'])
else:
    print("Error: Your system is not supported")
    exit(1)
