# Python 3.7
# Server program
# z5207825

# Require server.py and server_utility.py in the same directory for import
from server_utility import Forum
from socket import *
import threading
import sys
import time
import json

# application layer protocol: send messages structured in json format
# message = {
#     "cmd" : "",
#     "response": "",
#     "sender" : "",
#     "content" : ""
# }

if len(sys.argv) != 3:
    print("Usage: python3 server.py server_port admin_passwd")
    exit(1)

server_port = int(sys.argv[1])
admin_passwd = sys.argv[2]

# Creating a lock for multi-threading
t_lock = threading.Condition() 

# all clients dictionary
clients = {}

# online clients
online_clients = {}

# create Forum class
forum = Forum()

# forum online status
online = True

# Store initial users in the credentials file
def initialise_clients():
    with open("credentials.txt", 'r') as f:
        for line in f.readlines():
            line = line.strip()
            user, pwd = line.split()
            clients[user] = pwd


# Handle login (username/password) requests from new clients
def login_handler(clientConn, message):
    user = message['sender']
    response = ""
    if message['cmd'] == 'USERNAME':
        if user in online_clients:
            response = "ALREADY_IN"
            print(f"{user} has already logged in")
        elif user in clients:
            response = "OK"
        else:
            response = "NEW_USER"
            print("New User")

    # else:  cmd == 'PASSWORD'
    else:
        password = message['content']
        if user not in clients:
            # Add new client
            with open("credentials.txt", 'a') as f:
                f.write('\n' + user + ' ' + password)

            response = "OK"
            clients[user] = password
            online_clients[user] = clientConn
            print(f"{user} successful login")
        elif user in online_clients:
            response = "ALREADY_IN"
            print(f"{user} has already logged in")
        elif clients[user] == password:
            response = "OK"
            online_clients[user] = clientConn
            print(f"{user} successful login")
        else:
            response = "WRONG_PWD"
            print("Incorrect password")

    return response

# Handle client commands/requests
def client_handler(client):
    global online

    while True:
        received = client.recv(1024).decode()
        if not received:
            break

        message = json.loads(received)
        cmd = message['cmd']

        # Lock to prevent the access of shared data structures concurrently
        with t_lock:
            response = {'cmd': cmd, 'status': None, 'sender': 'SERVER', 'content': None}

            # Client Commands
            if cmd == 'USERNAME' or cmd == 'PASSWORD':
                response['status'] = login_handler(client, message)

            elif cmd == 'XIT':
                online_clients.pop(message['sender'])
                print(f"{message['sender']} exited")
                response['status'] = 'OK'

            elif cmd == 'CRT':
                print(f"{message['sender']} issued {cmd} command")
                if forum.create_forum_thread(message['content'], message['sender']):
                    response['status'] = 'OK'
                    print(f"Thread {message['content']} created by {message['sender']}")
                else:
                    response['status'] = 'THREAD_EXISTS'
                    print(f"Thread {message['content']} already exists")

            elif cmd == 'LST':
                print(f"{message['sender']} issued {cmd} command")
                response['status'] = 'OK'
                response['content'] = forum.get_active_threads()
            
            elif cmd == 'MSG':
                print(f"{message['sender']} issued {cmd} command")
                title = message['content']['title']
                msg = message['content']['message']
                if forum.thread_exists(title):
                    response['status'] = 'OK'
                    forum.add_message(title, message['sender'], msg)
                else:
                    response['status'] = 'NOT_EXIST'
                    print("Incorrect thread specified")
            
            elif cmd == 'RDT':
                print(f"{message['sender']} issued {cmd} command")
                if forum.thread_exists(message['content']):
                    response['status'] = 'OK'
                    response['content'] = forum.read_thread(message['content'])
                else:
                    response['status'] = 'NOT_EXIST'
                    print("Incorrect thread specified")

            elif cmd == 'EDT':
                print(f"{message['sender']} issued {cmd} command")
                title = message['content']['title']
                msg_No = int(message['content']['messageNo'])
                msg = message['content']['message']
                user = message['sender']
                if not forum.thread_exists(title):
                    response['status'] = 'NOT_EXIST'
                    print("Incorrect thread specified")
                elif forum.valid_msgNo(title, msg_No, user) != 'OK':
                    response['status'] = forum.valid_msgNo(title, msg_No, user)
                    print("Message cannot be edited")
                else:
                    response['status'] = 'OK'
                    forum.edit_message(title, user, msg_No, msg)

            elif cmd == 'DLT':
                print(f"{message['sender']} issued {cmd} command")
                title = message['content']['title']
                msg_No = int(message['content']['messageNo'])
                user = message['sender']
                if not forum.thread_exists(title):
                    response['status'] = 'NOT_EXIST'
                    print("Incorrect thread specified")
                elif forum.valid_msgNo(title, msg_No, user) != 'OK':
                    response['status'] = forum.valid_msgNo(title, msg_No, user)
                    print("Message cannot be deleted")
                else:
                    response['status'] = 'OK'
                    forum.delete_message(title, user, msg_No)

            elif cmd == 'UPD':
                print(f"{message['sender']} issued {cmd} command")
                title = message['content']['title']
                fname = message['content']['fileName']
                fsize = int(message['content']['fileSize'])
                if not forum.thread_exists(title):
                    response['status'] = 'NOT_EXIST'
                    print("Incorrect thread specified")
                else:
                    response['status'] = 'OK'

            elif cmd == 'DWN':
                print(f"{message['sender']} issued {cmd} command")
                title = message['content']['title']
                fname = message['content']['fileName']
                if not forum.thread_exists(title):
                    response['status'] = 'NOT_EXIST'
                    print("Incorrect thread specified")
                elif not forum.file_exist_in_thread(title, fname):
                    response['status'] = 'FILE_NOT_EXIST'
                    print(f"'{fname}' does not exist in Thread {title}")
                else:
                    response['status'] = 'OK'
                    response['content'] = forum.get_file_size(title, fname)

            elif cmd == 'RMV':
                print(f"{message['sender']} issued {cmd} command")
                title = message['content']
                if not forum.thread_exists(title):
                    response['status'] = 'NOT_EXIST'
                    print("Incorrect thread specified")
                elif forum.get_thread_creator(title) != message['sender']:
                    response['status'] = 'INVALID_USER'
                    print(f"Thread {title} cannot be removed by {message['sender']}")
                else:
                    response['status'] = 'OK'
                    forum.remove_thread(title)
                    print(f"Thread {title} removed")
            
            elif cmd == 'SHT':
                print(f"{message['sender']} issued {cmd} command")
                if message['content'] != admin_passwd:
                    response['status'] = 'INCORRECT_PWD'
                    print("Incorrect password")
                else:
                    forum.shutdown()
                    print("Server shutting down. Goodbye.")
                    online = False
                    break

            else:
                response['status'] = 'INVALID_CMD'

            client.send(json.dumps(response).encode())

            if cmd == 'UPD' and response['status'] == 'OK':
                forum.receive_file(client, title, message['sender'], fname, fsize)
            if cmd == 'DWN' and response['status'] == 'OK':
                forum.send_file(client, title, fname)

            t_lock.notify()


# Handle new clients connecting to server
def receive_handler():
    global t_lock
    global serverSocket
    global clients
    print("Waiting for clients ...")

    while True:
        conn, address = serverSocket.accept()
        print("Client connected")
        
        # create new thread for each new client connection socket
        t = threading.Thread(target=client_handler, args=(conn,))
        t.daemon = True
        t.start()
        


serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('localhost', server_port))
serverSocket.listen()

print(f"Forum started running on ip: {gethostbyname('localhost')} port: {server_port}")
initialise_clients()

t = threading.Thread(target=receive_handler)
t.daemon = True
t.start()

while online:
    time.sleep(0.1)
serverSocket.close()
