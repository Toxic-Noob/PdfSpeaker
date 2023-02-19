import os
import time
import json
import sys
import platform
import subprocess as sb
import shutil
import importlib.util
from addon import findPDF

# Globals
pdfPath = ""
pdfPages = []
startIndex = 0
indexEdited = False
pdfLength = 0
pageCount = None
textLang = "en"
speakOnly = False
printOnly = False
userDevice = "Android"
voiceId = 0

textTranslator = ""

libs = ["PyPDF2", "pyttsx3", "googletrans"]
columns = shutil.get_terminal_size().columns
command_history = []

# Setting up custom input to take input as a editable prompt
def takeInput(text):
    user_input = input(text)
    command_history.append(user_input)
    
    return user_input


# readline Library isn't exist in every environment, specially Windows. So, if exists, work else, don't give error
try:
    import readline
    # Set up readline module to enable line editing and command history
    readline.set_history_length(1000)
    readline.clear_history()

except:
    pass
    

# Print text with or without color. As, Windows cmd does not support escape symbols
def printC(text, end="\n"):
    if (userDevice == "Linux") or (userDevice == "Android"):
        text = text.replace("cWhite", "\033[37m").replace("cGreen", "\033[92m").replace("cRed", "\033[91m").replace("cBlue", "\033[94m")
    elif (userDevice == "Windows"):
        text = text.replace("cWhite", "").replace("cGreen", "").replace("cRed", "").replace("cBlue", "")
    
    print(text, end=end)

# Check for device
def checkDevice():
    global userDevice
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

# Formate the text. Sometimes PdfReader generates some problematic texts. We need to formate them for proper reading
def formatText(text):
    text = text.split(" ")
    newText = ""
    for i in range(len(text)):
        word = text[i]
        if (len(word.replace("\n", "")) > 1):
            newText += word + " "
            continue
        
        if (word == ""):
            newText += " "
        else:
            if (word == "I") or (word.lower() == "a"):
                if (len(text[i+1]) == 1):
                    newText += word
                else:
                    newText += word + " "
            else:
                newText += word
    
    # removing (-) to avoid misspelling
    newText = newText.replace("-\n", "").replace("  -  ", "").replace(" - ", "").replace(" -", "").replace("-", "").strip()
    return newText

# Show Help Message
def showHelp():
    time.sleep(0.3)
    print("\nWelcome to PdfSpeaker 1.0's Help Guide!")
    print("\n    /help\tShow this help message")
    print("\n    /info\tGet information of this Tool")
    print("\n    /find\tFind/Search PDF file path from your device via file name (Leave blank to find all PDF Files) (Only for Termux users)")
    print("\n    /file\tUse to Enter PDF File Path")
    print("\n    /start\tUse to start Reading")
    print("\n    /continue\tUse to Continue Reading from last PDF (Set custom settings first to avoid saved Settings)")
    print("\n    /history\tUse to get History for PDFs")
    print("\n    /page\tUse to specify reading Start page number")
    print("\n    /count\tUse to set the amount of pages to Read (Leave blank to reset)")
    print("\n    /lang\tUse to set a Translation Language. Give the language code (Default: en)")
    print("\n    /voice\tUse to change the voice to male or female. (0 for male, 1 for female || D: 0) (Only for PC Users)")
    print("\n    /speed\tUse to set the speed of speaking (slow/medium/fast || D: medium) (Only for PC users)")
    print("\n    /speakOnly\tUse to toggle Speak the Text only (true/false || D: false)")
    print("\n    /printOnly\tUse to toggle Print the Text only (true/false || D: false)")
    print("\n    /clear\tUse to Clear the Screen")
    print("\n    /reset\tUse to reset the PDF history")
    print("\n    /exit\tUse to exit Prompt\n")

# Show Tool Info
def showInfo():
    print("\nAuthor\t: ToxicNoob Inc.")
    print("Tool\t: PDF File Speaker")
    print("Version\t: 1.0.0")
    print("GitHub\t: https://github.com/toxic-noob")
    print("-"*10)
    print("ABOUT:")
    print("\n    This tool is created to Read out loud any PDF")
    print("    Supports Android(Termux), Linux, Windows(Beta)")
    print("    Runs in Background, Multi Functional\n")

# Save History
def saveHistory(pageNo):
    
    try:
        allData = json.loads(open("./addon/.history.json", "r").read())
    except:
        allData = json.loads("{}")
        allData.update({"pageHistory": {}, "bookHistory": {}})
    
    oldData = allData["pageHistory"]
    newData = {pdfPath: pageNo}
    oldData.update(newData)
    allData.update({"pageHistory": oldData})
    
    oldData = allData["bookHistory"]
    newData = {"path": pdfPath, "page": pageNo, "lang": textLang, "count": pageCount}
    oldData.update(newData)
    allData.update({"bookHistory": oldData})
    
    file = open("./addon/.history.json", "w")
    json.dump(allData, file)
    file.close()

# SetPage History
def setPageHistory():
    file = open("./addon/.history.json", "r")
    history = file.read()
    file.close()
    
    if not (history == ""):
        exists = json.loads(history).get("pageHistory")
        if (exists):
            pageNo = exists.get(pdfPath)
            if (pageNo):
                global startIndex
                startIndex = int(pageNo)

# Set Book History
def setBookHistory():
    file = open("./addon/.history.json", "r")
    history = file.read()
    file.close()
    
    if not (history == ""):
        bookHistory = json.loads(history).get("bookHistory")
        path = bookHistory.get("path")
        page = bookHistory.get("page")
        lang = bookHistory.get("lang")
        count = bookHistory.get("count")
        if (path and lang):
            global pdfPath, startIndex, textLang, pageCount
            pdfPath = path
            if not (indexEdited):
                startIndex = int(page)
            if (textLang == "en"):
                textLang = lang
            if (pageCount == None):
                pageCount = count
            return True
        else:
            print("No History Found") #error
            return False

# Get PDFs History
def getHistory():
    try:
        allData = json.loads(open("./addon/.history.json", "r").read())
    except:
        allData = json.loads("{}")
        allData.update({"pageHistory": {}, "bookHistory": {}})
    
    history = allData.get("pageHistory")
    
    return history

# Process PDF File from path
def processPdf(filePath, mode=1):
    global pdfPath, pdfPages, pdfLength
    
    pdfPath = filePath
    reader = PdfReader(pdfPath)
    pdfPages = reader.pages
    if (mode == 1):
        setPageHistory()
    pdfLength = len(pdfPages)
    

# Speak the text according to device
def speak(text):
    if (userDevice == "Linux") or (userDevice == "Windows"):
        engine.say(text)
        engine.runAndWait()
        returnCode = 0
    elif (userDevice == "Android"):
        returnCode = os.system("termux-tts-speak \"" + text + "\"")
    
    return returnCode


# Check and Speak PDF
def start():
    time.sleep(0.5)
    print("\n[Note] : To Stop process, press ctrl + c\n[Note] : Reading will not stop untill the page is Finished\n[Note] : If speaker not starts or skips page, it means that The PDF doesn't have any Text, instead Has Images or Blank.")
    printC("\n[cGreen*cWhite] Starting after (s):  ", end="")
    for i in [5, 4, 3, 2, 1, 0]:
        print("\b" + str(i), end = "", flush=1)
        time.sleep(1)
    print("\n")
    
    if (pageCount) and not (pageCount == 0):
        endIndex = startIndex + pageCount
    else:
        endIndex = pdfLength
    
    for i in range(startIndex, endIndex):
        saveHistory(i)
        try:
            pageText = pdfPages[i].extract_text()
        except:
            continue
        # Removing Dash (-) to avoid misspelling
        pageText = formatText(pageText)
        
        # Avoiding blank page
        if (pageText.replace("\n", "").replace(" ", "") == ""):
            continue
        
        if not (textLang == "en"):
            translator = textTranslator()
            
            try:
                pageText = translator.translate(pageText, dest=textLang).text
            except:
                print("No Internet Connection. Skipped Translation") #error
                pass
        
        printC("\n[cGreen*cWhite] Page No: cGreen" + str(i+1) + "\ncWhite")
        time.sleep(0.5)
        if not (speakOnly):
            print(pageText)
        # Removing new line to avoid useless Stops
        pageText = pageText.replace("\n", " ")
        if not (printOnly):
            returnCode = speak(pageText)
            if not (returnCode == 0):
                break
            
        else:
             time.sleep(1)
             input("\n\n[!] Press enter for next Page...")
    
    print("\n[*] Reading Finished\n")
    if (returnCode == 0):
        speak("Reading Finished")
    sys.exit()

# Check and Process Command
def checkCmd(cmdText):
    if (cmdText == ""):
        return
    
    cmd = cmdText.split(" ")[0]
    cmdArg = " ".join(cmdText.split(" ")[1:]).strip()
    
    # Find/Search PDF Files
    if (cmd == "/find"):
        if not (userDevice == "Android"):
            print("[!] Feature is for Termux Users only")
            return
        
        print("Press ctrl + c 2 times to stop searching")
        time.sleep(0.8)
        findPDF.start(cmdArg)
    
    # Get the file path
    elif (cmd == "/file"):
        if (cmdArg == ""):
            print("You must include a File Path") #error
            return
        
        if not (os.path.isfile(cmdArg)):
            print("No file Found in the given Path") #error
            return
        
        processPdf(cmdArg)
    
    # Set page no to start from
    elif (cmd == "/page"):
        if (cmdArg == "0") or (cmdArg == ""):
            cmdArg = "1"
        
        if not (cmdArg.isdigit()):
            print("Invalid Page Number") #error
            return
        
        global startIndex, indexEdited
        startIndex = int(cmdArg) - 1
        indexEdited = True
    
    # Set the pages amount to read
    elif (cmd == "/count"):
        if not (cmdArg.isdigit()) and not (cmdArg == ""):
            print("Invalid Amount") #error
            return
        if (cmdArg == ""):
            cmdArg = 0
        
        global pageCount
        pageCount = int(cmdArg)
    
    # Set translation language
    elif (cmd == "/lang"):
        if (cmdArg == ""):
            print("No Language Code given") #error
            return
        
        print("Testing...")
        global textTranslator
        try:
                translator = textTranslator()
        except:
                from googletrans import Translator
                textTranslator = Translator
                translator = textTranslator()
        
        try:
            testText = translator.translate("Test Successful", dest=cmdArg).text
            speak(testText)
        except Exception as e:
            if (isinstance(e, ValueError)):
                print("Invalid Language Code") #error
                return
            elif ("No address associated with hostname" in str(e)):
                print("Internet Connection is needed to Translate") #error
                return
            else:
                print("Internal Error Occured")
                return
        
        global textLang
        textLang = cmdArg
    
    # Change the voice
    elif (cmd == "/voice"):
        if (userDevice == "Android"):
            print("[!] Feature is for PC users Only")
            return
        
        global voiceId

        if (cmdArg == "") or (cmdArg == "0"):
            voiceId = 0
        elif (cmdArg == "1"):
            voiceId = 1
        else:
            print("Only 0 Or 1") #error
        
        try:
            engine.setProperty("voice", voices[voiceId].id)
        except:
            pass
    
    # Setting speaking speed
    elif (cmd == "/speed"):
        if (userDevice == "Android"):
            print("[!] Feature is for PC users Only")
            return
        
        if (cmdArg == "medium") or (cmdArg == ""):
            rate = 200
        elif (cmdArg == "slow"):
            rate = 150
        elif (cmdArg == "fast"):
            rate = 250
        else:
            print("Expected arguments are: slow/medium/fast")
            return
        
        engine.setProperty("rate", rate)
        
    
    # Toggle speak only
    elif (cmd == "/speakOnly"):
        global speakOnly
        if (cmdArg == "") or (cmdArg== "true"):
            speakOnly = True
        elif (cmdArg == "false"):
            speakOnly = False
        else:
            print("Only true Or false") #error
    
    # Toggle print only
    elif (cmd == "/printOnly"):
        global printOnly
        if (cmdArg == "") or (cmdArg == "true"):
            printOnly = True
        elif (cmdArg == "false"):
            printOnly = False
        else:
            print("Only true Or false") #error
    
    # Clear the screen
    elif (cmd == "/clear"):
        if (userDevice == "Linux") or (userDevice == "Android"):
            os.system("clear")
        elif (userDevice == "Windows"):
            os.system("cls")
    
    # Reset the current pdf history, not the Continue history
    elif (cmd == "/reset"):
        saveHistory(0)
        setPageHistory()
    
    # Show help Message
    elif (cmd == "/help"):
        showHelp()
    
    # Information of the Tool
    elif (cmd == "/info"):
        showInfo()
    
    # Start the show!
    elif (cmd == "/start"):
        if (pdfPath == ""):
            print("No PDF file path Setted") #error
            return
        
        if (startIndex > pdfLength):
            print("Invalid Start Page No: " + str(startIndex)) #error
            return
        
        try:
            start()
        except KeyboardInterrupt:
            print("\n\n[!] User Interrupt")
            return
    
    # Continue from the last reading
    elif (cmd == "/continue"):
        setted = setBookHistory()
    
        if (setted):
            processPdf(pdfPath, 2)
            if (startIndex > pdfLength):
                print("Invalid Start Page No: " + str(startIndex)) #error
                return
            
            try:
                start()
            except KeyboardInterrupt:
                print("\n\n[!] User Interrupt")
                return
    
    # Get the History of PDFs read
    elif (cmd == "/history"):
        history = getHistory()
        
        index = 1
        print("")
        for path in history.keys():
            printC(("[cGreen" + ("0" + str(index) if len(str(index))==1 else str(index)) + "cWhite]").center(columns+9))
            printC("\nPathcGreen: cWhite" + path)
            printC("PagecGreen: cWhite" + str(history.get(path)))
            print("")
            index += 1
    
    # Exit the program
    elif (cmd == "/exit"):
        sys.exit()
    
    else:
        print("Command not found: '" + cmd + "'. Type /help for Help Guide")


# Main Process
def main():
    print("PDF Speaker - A AlphaZ Production (Version: 1.0.0)")
    print("Type /help for More")
    while True:
        command = takeInput("#> ")
        checkCmd(command.strip())


if (__name__ == "__main__"):
    checkDevice()
    
    if not (os.path.isfile("./addon/.history.json")):
        if (userDevice == "Linux") or (userDevice == "Android"):
            os.system("touch ./addon/.history.json")
        elif (userDevice == "Windows"):
            os.system("echo. > .\\addon\\.history.json")
    
    absent = any(importlib.util.find_spec(x) is None for x in libs)
    if (userDevice == "Linux") or (userDevice == "Windows"):
        if (absent):
            printC("\n[cRed!cWhite] Required Packages not Found")
            print("Run: python setup.py\n")
            sys.exit()
        
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
        except:
            printC("\n[cRed!cWhite] pyttsx3 Library isn't installed properly\n")
            sys.exit()
            
    elif (userDevice == "Android"):
        if (sb.getoutput("command -v termux-tts-speak") == "") or (absent):
            printC("\n[cRed!cWhite] Required Packages not Found")
            print("Run: python setup.py\n")
            sys.exit()
    
    from PyPDF2 import PdfReader
    
    argvList = sys.argv
    if ("--help" in argvList) or ("-h" in argvList):
        checkCmd("/help")
        sys.exit()
    elif ("--version" in argvList) or ("-v" in argvList):
        print("PDFSpeaker 1.0.0")
        sys.exit()
    
    try:
        main()
    except KeyboardInterrupt:
       print("\n\n[!] User Interrupt\n")