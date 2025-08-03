#!/usr/bin/env python3

import os
import subprocess

os.system("clear")
input("Press Enter to continue...")
print("Starting script...")

# Update system
os.system("sudo apt update && sudo apt upgrade -y")

# Install Apache
input("Press Enter to install Apache...")
print("Installing Apache...")
os.system("sudo apt install apache2 -y")
os.system("sudo systemctl enable --now apache2")

# Install MariaDB
input("Press Enter to install MariaDB...")
print("Installing MariaDB...")
os.system("sudo apt install mariadb-server -y")
os.system("sudo systemctl enable --now mariadb")
os.system("sudo mysql_secure_installation")

# Install PHP and modules
input("Press Enter to install PHP...")
print("Installing PHP and modules...")
os.system("sudo apt install php libapache2-mod-php php-mysql -y")
os.system("sudo systemctl restart apache2")

# Create Database for MariaDB
input("Press Enter to continue...")
print("Creating database for MariaDB")

database_name = input('Database name: ')
database_user = input('Database username: ')
database_passwd = input('Database user password: ')

command = (
    f"sudo mysql -u root -p -e "
    f"'CREATE DATABASE {database_name}; "
    f"CREATE USER '{database_user}'@'localhost' IDENTIFIED BY '{database_passwd}'; "
    f"GRANT ALL PRIVILEGES ON {database_name}.* TO '{database_user}'@'localhost'; "
    f"FLUSH PRIVILEGES;'"
)
os.system(command)

# Configure UFW firewall
input("Press Enter to configure UFW...")
print("Configuring UFW firewall...")
os.system("sudo ufw allow 3306/tcp")
os.system("sudo ufw enable")

print("Add HTTP (80) and HTTPS (443) ports?")
ufw_port = input("Answer (1 = yes, 0 = no): ")

if ufw_port == "1":
    os.system("sudo ufw allow 80/tcp")
    os.system("sudo ufw allow 443/tcp")
    print("Success: Ports 80 (HTTP) and 443 (HTTPS) are now open")
else:
    print("Skipped port configuration")

# Verify installation
print("Test Apache installation?")
checkout_answer = input("Answer (1 = yes, 0 = no): ")

if checkout_answer == "1":
    print("Testing Apache service...")
    os.system("curl -I localhost")
else:
    print("Installation complete!")
    subprocess.run(["python3", "menu.py"])




