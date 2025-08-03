#!/usr/bin/env python3

import os
import subprocess

os.system("clear")
input("Press Enter to continue...")
print("Starting script...")

# System update
os.system("sudo dnf upgrade -y")

# Install Apache (httpd)
input("Press Enter to install Apache(httpd)...")
print("Installing Apache...")
os.system("sudo dnf install httpd -y")
os.system("sudo systemctl enable --now httpd")

# Install MariaDB
input("Press Enter to install MariaDB...")
print("Installing MariaDB...")
os.system("sudo dnf install mariadb-server -y")
os.system("sudo systemctl enable --now mariadb")
os.system("sudo mariadb-secure-installation")

# Install PHP and modules
input("Press Enter to install PHP...")
print("Installing PHP and modules...")
os.system("sudo dnf install php php-mysqlnd -y")
os.system("sudo systemctl restart httpd")

# Create MariaDB database
input("Press Enter to create database...")
print("Creating database")

database_name = input('Database name: ')
database_user = input('Database username: ')
database_passwd = input('User password: ')

db_command = (
    f"sudo mysql -u root -p -e "
    f"\"CREATE DATABASE {database_name}; "
    f"CREATE USER '{database_user}'@'localhost' IDENTIFIED BY '{database_passwd}'; "
    f"GRANT ALL PRIVILEGES ON {database_name}.* TO '{database_user}'@'localhost'; "
    f"FLUSH PRIVILEGES;\""
)
os.system(db_command)

# Configure firewall
input("Press Enter to configure firewall...")
print("Configuring firewall...")
os.system("sudo firewall-cmd --add-service=http --permanent")
os.system("sudo firewall-cmd --add-service=https --permanent")
os.system("sudo firewall-cmd --add-port=3306/tcp --permanent")
os.system("sudo firewall-cmd --reload")

# Configure HTTP/HTTPS ports

print("add to firewall http (80) and https (443) ports?")
enable_ports = int(input("Add these ports to firewall? (1 = yes, 0 = no): "))

if enable_ports == 1:
    print("Adding standard web ports...")
    os.system("sudo firewall-cmd --add-port=80/tcp --permanent")
    os.system("sudo firewall-cmd --add-port=443/tcp --permanent")
    os.system("sudo firewall-cmd --reload")
    print("Success: Ports 80 (http) and 443 (https) oppening now")
else:
    print("Skipping standard web ports configuration")

# Verify Apache installation
print("Test Apache installation?")
checkout_answer = int(input("Answer (1 = yes, 0 = no): "))
if checkout_answer == 1:
    print("Testing Apache...")
    os.system("curl -I localhost")
else:
    print("Complete!")
    subprocess.run(["python3", "menu.py"])
