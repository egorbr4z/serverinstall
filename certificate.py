#!/usr/bin/env python3
import os
import subprocess

# Check system
def detect_distro():
    """Detect Linux distribution"""
    if os.path.exists('/etc/debian_version'):
        return 'debian'
    elif os.path.exists('/etc/arch-release'):
        return 'arch'
    elif os.path.exists('/etc/fedora-release'):
        return 'fedora'
    else:
        return 'unknown'

def install_certbot_debian():
    """Install Certbot on Debian/Ubuntu"""
    print("\nInstalling Certbot for Debian/Ubuntu...")
    os.system("sudo apt update")
    os.system("sudo apt install certbot python3-certbot-apache -y")
    print("Certbot installed successfully!")

def install_certbot_arch():
    """Install Certbot on Arch Linux"""
    print("\nInstalling Certbot for Arch...")
    os.system("sudo pacman -S certbot certbot-apache --noconfirm")
    print("Certbot installed successfully!")

def install_certbot_fedora():
    """Install Certbot on Fedora"""
    print("\nInstalling Certbot for Fedora...")
    os.system("sudo dnf install certbot python3-certbot-apache -y")
    print("Certbot installed successfully!")

# Code
os.system("clear")
print("=== Let's Encrypt Certbot Installer ===")

distro = detect_distro()
print(f"\nDetected system: {distro.capitalize()}")
input("Press Enter to continue...")

if distro == 'debian':
    install_certbot_debian()
elif distro == 'arch':
    install_certbot_arch()
elif distro == 'fedora':
    install_certbot_fedora()
else:
    print("\n\033[91mError: Unsupported system detected\033[0m")
    exit(1)

print("To get a certificate, run: ")
print("\n\033[91msudo certbot --apache\033[0m")
