#!/usr/bin/env python3

import os
import subprocess

def show_menu():
    os.system("clear")
    print("=== Main Menu ===")
    print("1. Install Let's Encrypt Certificate")
    print("2. Exit")
    return input("\nSelect an option (1-2): ")

def run_certbot():
    subprocess.run(["python3", "certificate.py"])
    input("\nPress Enter to return to menu...")

while True:
    choice = show_menu()
    
    if choice == "1":
        run_certbot()
    elif choice == "2":
        print("\nExiting...")
        break
    else:
        print("Invalid choice. Please try again.")
        input("Press Enter to continue...")
