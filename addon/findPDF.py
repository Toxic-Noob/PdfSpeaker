import os
from sys import stdout, argv

# Count the amount of searched and found
count = 1
found = 0

# Search
def search(hint, root="/sdcard/", text = "ytd"):
    global count, found
    path = root+"/"+hint
    if os.path.isfile(path):
        if (text in hint.lower()):
            if (path.endswith(".pdf")):
                stdout.write("\r" + path.replace("/data/data/com.termux/files/home", "$HOME") + "              \n\n")
                stdout.flush()
                found += 1
        
        stdout.write("\r[ Searched / Found ]: [ " + str(count) + " / " + str(found) + " ]")
        count += 1
    elif os.path.isdir(path):
        try:
            for dirc in os.listdir(path):
                search(dirc, path, text)
        except IOError:
            pass


def start(text):
    path = ["/sdcard", "/storage"]
    print("\n[\033[92m*\033[37m] Searching For: " + ("Every PDF" if text == "" else text) + "\n")
    
    if (type(path) == str):
        path = [path]
    
    if (text == ""):
        text = ".pdf"
    
    for root in path:
        try:
            for dirc in os.listdir(root):
                if (dirc == "storage"):
                    continue
                 
                search(dirc, root, text)
        
        except:
            pass

    print("\n")
