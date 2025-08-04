#!/usr/bin/env python3
import os
import subprocess

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

def debian_operations():
   #  Operations for Debian/Ubuntu
    def toggle_site():
        site = input("Enter site name to enable/disable: ")
        conf_path = f"/etc/apache2/sites-available/{site}.conf"
        if os.path.exists(conf_path):
            action = input("Enable? (1=Yes, 0=No): ")
            if action == "1":
                subprocess.run(["sudo", "a2ensite", site])
            elif action == "0":
                subprocess.run(["sudo", "a2dissite", site])
            subprocess.run(["sudo", "systemctl", "reload", "apache2"])
        else:
            print("Site config not found!")
        input("Press Enter to continue...")

    def view_logs():
        subprocess.run(["sudo", "tail", "-n", "20", "/var/log/apache2/error.log"])
        input("Press Enter to continue...")

    def create_vhost():
        domain = input("Enter domain name: ")
        docroot = input(f"Document root (/var/www/{domain}): ") or f"/var/www/{domain}"
        
        vhost_conf = f"""<VirtualHost *:80>
    ServerName {domain}
    DocumentRoot {docroot}
    ErrorLog ${{APACHE_LOG_DIR}}/{domain}-error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain}-access.log combined
    <Directory {docroot}>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>"""
        
        with open(f"/etc/apache2/sites-available/{domain}.conf", "w") as f:
            f.write(vhost_conf)
        
        os.makedirs(docroot, exist_ok=True)
        subprocess.run(["sudo", "chown", "-R", "www-data:www-data", docroot])
        print(f"Virtual host created for {domain}")
        input("Press Enter to enable site...")
        subprocess.run(["sudo", "a2ensite", domain])
        subprocess.run(["sudo", "systemctl", "reload", "apache2"])

    return {
        'toggle_site': toggle_site,
        'view_logs': view_logs,
        'create_vhost': create_vhost,
        'service_name': 'apache2',
        'config_test': ['apache2ctl', 'configtest']
    }

def arch_operations():
    # Operations for Arch Linux
    def toggle_site():
        site = input("Enter site name to enable/disable: ")
        conf_path = f"/etc/httpd/conf/extra/{site}.conf"
        if os.path.exists(conf_path):
            action = input("Enable? (1=Yes, 0=No): ")
            if action == "1":
                subprocess.run(["sudo", "ln", "-sf", conf_path, "/etc/httpd/conf/sites-enabled/"])
            elif action == "0":
                subprocess.run(["sudo", "rm", "-f", f"/etc/httpd/conf/sites-enabled/{site}.conf"])
            subprocess.run(["sudo", "systemctl", "reload", "httpd"])
        else:
            print("Site config not found!")
        input("Press Enter to continue...")

    def view_logs():
        subprocess.run(["sudo", "tail", "-n", "20", "/var/log/httpd/error.log"])
        input("Press Enter to continue...")

    def create_vhost():
        domain = input("Enter domain name: ")
        docroot = input(f"Document root (/srv/http/{domain}): ") or f"/srv/http/{domain}"
        
        vhost_conf = f"""<VirtualHost *:80>
    ServerName {domain}
    DocumentRoot {docroot}
    ErrorLog /var/log/httpd/{domain}-error.log
    CustomLog /var/log/httpd/{domain}-access.log combined
    <Directory {docroot}>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>"""
        
        with open(f"/etc/httpd/conf/extra/{domain}.conf", "w") as f:
            f.write(vhost_conf)
        
        os.makedirs(docroot, exist_ok=True)
        subprocess.run(["sudo", "chown", "-R", "http:http", docroot])
        print(f"Virtual host created for {domain}")
        input("Press Enter to enable site...")
        subprocess.run(["sudo", "ln", "-sf", f"/etc/httpd/conf/extra/{domain}.conf", 
                       "/etc/httpd/conf/sites-enabled/"])
        subprocess.run(["sudo", "systemctl", "reload", "httpd"])

    return {
        'toggle_site': toggle_site,
        'view_logs': view_logs,
        'create_vhost': create_vhost,
        'service_name': 'httpd',
        'config_test': ['apachectl', 'configtest']
    }

def fedora_operations():
    # Operations for Fedora
    def toggle_site():
        site = input("Enter site name to enable/disable: ")
        conf_path = f"/etc/httpd/conf.d/{site}.conf"
        if os.path.exists(conf_path):
            action = input("Enable? (1=Yes, 0=No): ")
            if action == "1":
                if os.path.exists(f"{conf_path}.disabled"):
                    subprocess.run(["sudo", "mv", f"{conf_path}.disabled", conf_path])
            elif action == "0":
                subprocess.run(["sudo", "mv", conf_path, f"{conf_path}.disabled"])
            subprocess.run(["sudo", "systemctl", "reload", "httpd"])
        else:
            print("Site config not found!")
        input("Press Enter to continue...")

    def view_logs():
        subprocess.run(["sudo", "tail", "-n", "20", "/var/log/httpd/error_log"])
        input("Press Enter to continue...")

    def create_vhost():
        domain = input("Enter domain name: ")
        docroot = input(f"Document root (/var/www/{domain}): ") or f"/var/www/{domain}"
        
        vhost_conf = f"""<VirtualHost *:80>
    ServerName {domain}
    DocumentRoot {docroot}
    ErrorLog /var/log/httpd/{domain}-error_log
    CustomLog /var/log/httpd/{domain}-access_log combined
    <Directory {docroot}>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>"""
        
        with open(f"/etc/httpd/conf.d/{domain}.conf", "w") as f:
            f.write(vhost_conf)
        
        os.makedirs(docroot, exist_ok=True)
        subprocess.run(["sudo", "chown", "-R", "apache:apache", docroot])
        print(f"Virtual host created for {domain}")
        subprocess.run(["sudo", "systemctl", "reload", "httpd"])

    return {
        'toggle_site': toggle_site,
        'view_logs': view_logs,
        'create_vhost': create_vhost,
        'service_name': 'httpd',
        'config_test': ['apachectl', 'configtest']
    }

def show_menu(ops):
    """Show main menu"""
    os.system("clear")
    print("=== Apache Configuration Menu ===")
    print("1. Install Let's Encrypt Certificate")
    print("2. Enable/Disable Site")
    print("3. Test Configuration")
    print("4. Restart Apache")
    print("5. Check Apache Status")
    print("6. View Error Logs")
    print("7. Create New Virtual Host")
    print("8. Exit")
    return input("\nSelect an option (1-8): ")

# Main execution starts here
distro = detect_distro()

if distro == 'debian':
    ops = debian_operations()
elif distro == 'arch':
    ops = arch_operations()
elif distro == 'fedora':
    ops = fedora_operations()
else:
    print("Unsupported distribution!")
    exit(1)

while True:
    choice = show_menu(ops)
    
    if choice == "1":
        subprocess.run(["python3", "certificate.py"])
    elif choice == "2":
        ops['toggle_site']()
    elif choice == "3":
        subprocess.run(["sudo"] + ops['config_test'])
    elif choice == "4":
        subprocess.run(["sudo", "systemctl", "restart", ops['service_name']])
    elif choice == "5":
        subprocess.run(["sudo", "systemctl", "status", ops['service_name']])
    elif choice == "6":
        ops['view_logs']()
    elif choice == "7":
        ops['create_vhost']()
    elif choice == "8":
        print("\nExiting...")
        break
    else:
        print("Invalid option!")
    
    if choice in ["1","2","3","4","5","6","7"]:
        input("Press Enter to continue...")
