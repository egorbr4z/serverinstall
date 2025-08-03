#!/usr/bin/env python3

import os
import subprocess

os.system("clear")
input("Press Enter to continue...")
print("Starting script...")

# Update system
os.system("sudo pacman -Syu --noconfirm")

# Install Apache
input("Press Enter to install Apache(httpd)...")
print("Installing Apache...")
os.system("sudo pacman -S apache --noconfirm")
os.system("sudo systemctl enable --now httpd")

# Install MariaDB
input("Press Enter to install MariaDB...")
print("Installing MariaDB...")
os.system("sudo pacman -S mariadb --noconfirm")
os.system("sudo systemctl enable --now mariadb")
os.system("sudo mariadb-secure-installation")

# Install PHP and modules
input("Press Enter to install PHP...")
print("Installing PHP and modules...")
os.system("sudo pacman -S php php-apache php-mysql --noconfirm")

# Configure Apache to use PHP
os.system("sudo sed -i 's/LoadModule mpm_event_module modules\/mod_mpm_event.so/#LoadModule mpm_event_module modules\/mod_mpm_event.so/' /etc/httpd/conf/httpd.conf")
os.system("sudo sed -i 's/#LoadModule mpm_prefork_module modules\/mod_mpm_prefork.so/LoadModule mpm_prefork_module modules\/mod_mpm_prefork.so/' /etc/httpd/conf/httpd.conf")
os.system("sudo sed -i '/LoadModule dir_module modules\/mod_dir.so/a LoadModule php_module modules\/libphp.so'" + " /etc/httpd/conf/httpd.conf")
os.system("sudo systemctl restart httpd")

# Create Database for MariaDB
input("Press Enter to continue...")
print("Create database for MariaDB")

database_name = input('Database name: ')
database_user = input('Database username: ')
database_passwd = input('Database user password: ')

database = (
    f"sudo mysql -u root -p -e "
    f"'CREATE DATABASE {database_name}; "
    f"CREATE USER `{database_user}`@`localhost` IDENTIFIED BY '{database_passwd}'; "
    f"GRANT ALL PRIVILEGES ON {database_name}.* TO `{database_user}`@`localhost`; "
    f"FLUSH PRIVILEGES;'"
)

os.system(database)

# Firewall configuration
input("Press Enter to configure firewall...")
print("Configuring firewall...")
os.system("sudo firewall-cmd --add-port=3306/tcp --permanent")
os.system("sudo firewall-cmd --reload")

print("Add HTTP (80) and HTTPS (443) ports?")
ufw_port = input("Answer (1 = yes, 0 = no): ")

if ufw_port == "1":
    os.system("sudo firewall-cmd --add-port=80/tcp --permanent")
    os.system("sudo firewall-cmd --add-port=443/tcp --permanent")
    os.system("sudo firewall-cmd --reload")
    print("Ports 80 and 443 added to firewall")
else:
    print("Skipping HTTP/HTTPS ports")

# Verify installation
print("Test Apache installation?")
checkout_answer = input("Answer (1 = yes, 0 = no): ")
if checkout_answer == "1":
    print("Testing Apache service...")
    os.system("curl -I localhost")
else:
    print("Installation complete!")
    subprocess.run(["python3", "menu.py"])
