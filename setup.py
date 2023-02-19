import os
import subprocess as sb
import platform
import sys

def getDevice():
    system = platform.system()
    if (system == "Linux"):
        if hasattr(sys, "getandroidapilevel"):
            userDevice = "Android"
        else:
            userDevice = "Linux"
    elif (system == "Windows"):
        userDevice = "Windows"
    else:
        print("Your Device is Unrecognized")
        sys.exit()
    
    return userDevice

print("[!] Stand By, Installing packages...\n")

userDevice = getDevice()

os.system("pip install PyPDF2")
os.system("pip install googletrans")
os.system("pip install pyttsx3")
os.system("termux-setup-storage")


if (userDevice == "Android"):
    if (sb.getoutput("command -v termux-tts-speak") == ""):
        os.system("pkg install termux-api")
        print("\n[!] Please install Termux-api apk from the link below in your device to work perfectly")
        print("[!] The main feature requires Termux-api to be Installed")
        print("[!] APK Link: https://f-droid.org/repo/com.termux.api_51.apk")
        print("\n[*] Don't worry, the app is secure ;)\n")

print("\n[!] Installation Complete!\n")
