#!/usr/bin/env python3

import os
import subprocess

os.system("clear")
input("Press Enter to continiune...")
print("Starting scrypt...")

# Updating system
os.system("sudo apt update && sudo apt upgrade -y")

# Installing Apache2
input("Press Enter to install Apache...")
print("Installing Apache2...")

os.system("sudo apt install apache2 -y && sudo systemctl enable --now apache2")

# Installing MariaDB
input("Press Enter to install MariaDB...")
print("Installing MariaDB...")

os.system("sudo apt install mariadb-server -y"
"sudo systemctl enable --now mariadb"
"sudo mysql_secure_installation"
)

# Installing PHP
input("Press Enter to install PHP...")
print("Installing PHP and modules...")

os.system("sudo apt install php libapache2-mod-php php-mysql -y")

# Create Database for MariaDB
input("Press Enter to continiune...")
print("Create database for MariaDB")

print("Write a name of database")
database_name = input('Name of database: ')

print("Write a name of database user")
database_user = input('Name of database user: ')

print("Write a password for database user")
database_passwd = input('Password for database user: ')

command = (
    f"sudo mysql -u root -p -e "
    f"'CREATE DATABASE {database_name}; "
    f"CREATE USER \"{database_user}\"@\"localhost\" IDENTIFIED BY \"{database_passwd}\"; "
    f"GRANT ALL PRIVILEGES ON {database_name}.* TO \"{database_user}\"@\"localhost\"; "
    f"FLUSH PRIVILEGES;'"
    f"EXIT;"
)

os.system(command)

# Ufw
input("Press Enter to install and enable ufw")
print("Enable ufw")


