# Python 3.7
# Client program
# z5207825

from socket import *
import threading
import sys
import json
import time
import os

# application layer protocol
# message = {
#     "cmd" : "",
#     "sender" : "",
#     "content" : ""
# }

if len(sys.argv) != 3:
    print("Usage: python3 client.py server_IP server_port")
    exit(1)

username = None
password = None
online = True

# Prompt the user to input command
def prompt():
    msg = "Enter one of the following commands: " \
          "CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT\n" \
          f"{username}: "
    return input(msg)

# Checking if user input is valid
def valid_input(cmd, actual, expected):
    if len(actual) != expected:
        print(f"Incorrect syntax for {cmd}")
        return False
    return True

# Handle client username login
def login_username():
    global username
    global password

    username = input('Enter username: ')
    message = {'cmd': 'USERNAME', 'sender': username, 'content': None}

    # Send username to server
    clientSocket.send(json.dumps(message).encode())

    # Get server response from username
    response = clientSocket.recv(1024).decode()
    response = json.loads(response)

    status = response['status']
    if status == 'OK':
        password = input('Enter password: ')
    elif status == "ALREADY_IN":
        print(f"{username} has already logged in")
        login_username()
    elif status == "NEW_USER":
        password = input(f'Enter password for new user {username}: ')
    else:
        print("ERROR")
        exit(1)

# Handle client password login
def login_password():
    # password should contain a value at this stage
    if password == None:
        exit(1)

    # Send password to the server for the username
    message = {'cmd': 'PASSWORD', 'sender': username, 'content': password}
    clientSocket.send(json.dumps(message).encode())

    # Get server response from password request
    response = clientSocket.recv(1024).decode()
    response = json.loads(response)

    status = response['status']
    if status == 'OK':
        print("\nWelcome to the forum!")
    elif status == "WRONG_PWD":
        print("Invalid Password! Please try again.\n")
        login_username()
        login_password()
    elif status == "ALREADY_IN":
        print(f"{username} has already logged in\n")
        login_username()
        login_password()
    else:
        print("ERROR")
        exit(1)

# Handle user input to send to server
def send_handler(line):
    global online
    
    cmd = line[:3]
    args = line.split()
    msg = {'cmd': cmd, 'sender': username, 'content': None}
    if cmd == 'XIT':
        if not valid_input(cmd, args, 1): return None
        online = False
    elif cmd == 'CRT':
        if not valid_input(cmd, args, 2): return None
        _, title = line.split()
        msg['content'] = title
    elif cmd == 'LST':
        if not valid_input(cmd, args, 1): return None
    elif cmd == 'MSG':
        args = line.split(' ', 2)
        if not valid_input(cmd, args, 3): return None
        _, title, message = line.split(' ', 2)
        msg['content'] = {'title': title, 'message': message}
    elif cmd == 'RDT':
        if not valid_input(cmd, args, 2): return None
        _, title = line.split()
        msg['content'] = title
    elif cmd == 'EDT':
        args = line.split(' ', 3)
        if not valid_input(cmd, args, 4): return None
        _, title, msg_no, message = line.split(' ', 3)
        msg['content'] = {'title': title, 'messageNo': msg_no, 'message': message}
    elif cmd == 'DLT':
        if not valid_input(cmd, args, 3): return None
        _, title, msg_no = line.split()
        msg['content'] = {'title': title, 'messageNo': msg_no}
    elif cmd == 'UPD':
        if not valid_input(cmd, args, 3): return None
        _, title, fname = line.split()
        fsize = os.path.getsize(fname)
        msg['content'] = {'title': title, 'fileName': fname, 'fileSize':fsize}
    elif cmd == 'DWN':
        if not valid_input(cmd, args, 3): return None
        _, title, fname = line.split()
        msg['content'] = {'title': title, 'fileName': fname}
    elif cmd == 'RMV':
        if not valid_input(cmd, args, 2): return None
        _, title = line.split()
        msg['content'] = title
    elif cmd == 'SHT':
        if not valid_input(cmd, args, 2): return None
        _, admin_pwd = line.split()
        msg['content'] = admin_pwd

    else:
        print("Invalid command. Please try again.")
        return None

    clientSocket.send(json.dumps(msg).encode())
    return msg


# Handle response from server
def receive_handler(msg):
    global online

    response = clientSocket.recv(1024).decode()
    if len(response) == 0: 
            online = False
            print("Goodbye. Server shutting down")
            return

    response = json.loads(response)

    if response['cmd'] == 'CRT':
        if response['status'] == 'OK':
            print(f"Thread '{msg['content']}' created")
        if response['status'] == 'THREAD_EXISTS':
            print(f"Thread '{msg['content']}' already exists")

    elif response['cmd'] == 'XIT':
        print(f"Goodbye {username}!")

    elif response['cmd'] == 'LST':
        thread_list = response['content']
        if len(thread_list) == 0:
            print("No threads to list")
        else:
            print("The list of active threads: ")
            for title in thread_list:
                print(title)

    elif response['cmd'] == 'MSG':
        if response['status'] == 'OK':
            print(f"Message posted to '{msg['content']['title']}' thread")
        if response['status'] == 'NOT_EXIST':
            print(f"Thread '{msg['content']['title']}' does not exist")

    elif response['cmd'] == 'RDT':
        if response['status'] == 'OK':
            thread_msgs = response['content']
            if len(thread_msgs) == 0:
                print(f"Thread '{msg['content']}' is empty")
            else:
                for line in thread_msgs:
                    print(line)
        if response['status'] == 'NOT_EXIST':
            print(f"Thread '{msg['content']}' does not exist")
    
    elif response['cmd'] == 'EDT':
        if response['status'] == 'OK':
            line = f"Message {msg['content']['messageNo']} in Thread " \
                   f"'{msg['content']['title']}' has been edited"
            print(line)
        elif response['status'] == 'INVALID_MSG_NUM':
            line = f"The message number {msg['content']['messageNo']} does not " \
                   f"belong in Thread '{msg['content']['title']}'"
            print(line)
        elif response['status'] == 'INVALID_USER':
            print("The message belongs to another user and cannot be edited")
        elif response['status'] == 'NOT_EXIST':
            print(f"Thread '{msg['content']['title']}' does not exist")
    
    elif response['cmd'] == 'DLT':
        if response['status'] == 'OK':
            line = f"Message {msg['content']['messageNo']} in Thread " \
                   f"'{msg['content']['title']}' has been deleted"
            print(line)
        elif response['status'] == 'INVALID_MSG_NUM':
            line = f"The message number {msg['content']['messageNo']} does not " \
                   f"belong in Thread '{msg['content']['title']}'"
            print(line)
        elif response['status'] == 'INVALID_USER':
            print("The message belongs to another user and cannot be deleted")
        elif response['status'] == 'NOT_EXIST':
            print(f"Thread '{msg['content']['title']}' does not exist")
    
    elif response['cmd'] == 'UPD':
        if response['status'] == 'NOT_EXIST':
            print(f"Thread '{msg['content']['title']}' does not exist")
        elif response['status'] == 'OK':
            with open(msg['content']['fileName'], 'rb') as f:
                upload = f.read()
            clientSocket.sendall(upload)
            print(f"{username} uploaded '{msg['content']['fileName']}'")
    
    elif response['cmd'] == 'DWN':
        if response['status'] == 'NOT_EXIST':
            print(f"Thread '{msg['content']['title']}' does not exist")
        elif response['status'] == 'FILE_NOT_EXIST':
            print(f"File does not exist in Thread {msg['content']['title']}")
        else:
            fsize = int(response['content'])
            curr_size = 0
            with open(msg['content']['fileName'], 'wb') as f:
                while curr_size < fsize:
                    upload = clientSocket.recv(4096)
                    curr_size += len(upload)
                    f.write(upload)
            
            print(f"{msg['content']['fileName']} successfully downloaded")
    
    elif response['cmd'] == 'RMV':
        if response['status'] == 'NOT_EXIST':
            print(f"Thread '{msg['content']}' does not exist")
        elif response['status'] == 'INVALID_USER':
            print("The thread was created by another user and cannot be removed")
        else:
            print(f"Thread '{msg['content']}' removed")

    elif response['cmd'] == 'SHT':
        if response['status'] == 'INCORRECT_PWD':
            print("Incorrect password")


def client_session():
    global online
    while online:
        print()
        line = prompt().strip()
        msg = send_handler(line)
        if not msg:
            continue
        receive_handler(msg)


server_IP = sys.argv[1]
server_port = int(sys.argv[2])

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((server_IP, server_port))

login_username()
login_password()
client_session()
clientSocket.close()
