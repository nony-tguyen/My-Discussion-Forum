from socket import *
import os

# Forum object which manages all threads created by users in this forum
class Forum:
    def __init__(self):
        self.threads = {}

    # Create a new thread, if thread already exists return False otherwise True
    def create_forum_thread(self, title, user):
        if title in self.threads:
            return False
        else:
            self.threads[title] = ForumThread(title, user)
            return True
    
    def get_active_threads(self):
        return list(self.threads.keys())

    def thread_exists(self, title):
        if title in self.threads:
            return True
        else:
            return False
    
    def add_message(self, title, user, msg):
        self.threads[title].add_message(user, msg)

    def read_thread(self, title):
        return self.threads[title].read_messages()

    def valid_msgNo(self, title, msg_no, user):
        t = self.threads[title]
        if not t.contains_msgNo(msg_no):
            return 'INVALID_MSG_NUM'
        elif t.get_user_by_msgNo(msg_no) != user:
            return 'INVALID_USER'
        else:
            return 'OK'
    
    def file_exist_in_thread(self, title, fname):
        return self.threads[title].does_file_exist(fname)
    
    def edit_message(self, title, user, msg_no, msg):
        self.threads[title].edit_message(user, msg_no, msg)
    
    def delete_message(self, title, user, msg_no):
        self.threads[title].delete_message(user, msg_no)
    
    def receive_file(self, clientSocket, title, user, fname, fsize):
        self.threads[title].add_file(clientSocket, user, fname, fsize)
    
    def send_file(self, clientSocket, title, fname):
        self.threads[title].send_file(clientSocket, fname)

    def get_file_size(self, title, fname):
        return self.threads[title].get_file_size(fname)

    def get_thread_creator(self, title):
        return self.threads[title].creator
    
    def remove_thread(self, title):
        self.threads[title].remove_thread()
        del self.threads[title]
    
    def shutdown(self):
        for t in list(self.threads.keys()):
            self.remove_thread(t)
        os.remove('credentials.txt')


# ForumThread object contains methods to manage an individual thread
class ForumThread:
    def __init__(self, title, user):
        self.title = title
        self.creator = user
        self.messages = {}
        self.files = {}
        self.curr_msgNo = 1
        self.curr_fileNo = 1
        self.create_thread_file()

    def create_thread_file(self):
        with open(self.title, 'w') as f:
            f.write(f"Started by: {self.creator}")

    def remove_thread(self):
        for f in self.files:
            os.remove(self.title + '-' + f)
        os.remove(self.title)

    def add_message(self, user, msg):
        entry = (self.curr_msgNo, user)
        self.messages[entry] = msg.rstrip()
        with open(self.title, 'a') as f:
            f.write(f"\n{self.curr_msgNo} {user}: {msg.rstrip()}")
        print(f"Message posted to {self.title} thread")
        self.curr_msgNo += 1

    def add_file(self, client, user, fname, fsize):
        self.files[fname] = user
        entry = ('f'+str(self.curr_fileNo), user)
        self.messages[entry] = fname
        self.curr_fileNo += 1
        with open(self.title, 'a') as f:
            f.write(f"\n{user} uploaded {fname}")
        
        # Reading in stream of bytes from clientSocket and
        # writing into new file at server directory
        curr_size = 0
        fileName = self.title + '-' + fname
        with open(fileName, 'wb') as f:
            while curr_size < fsize:
                upload = client.recv(4096)
                curr_size += len(upload)
                f.write(upload)
        
        print(f"{user} uploaded file '{fname}' to {self.title} thread")

    def read_messages(self):
        with open(self.title, 'r') as f:
            lines = f.readlines()[1:]
        print(f"Thread {self.title} read")
        return [l.rstrip() for l in lines]

    def edit_message(self, user, msg_no, new_msg):
        usr = self.get_user_by_msgNo(msg_no)
        self.messages[(msg_no, usr)] = new_msg
        self.write_to_file()
        print(f"Message {msg_no} in Thread {self.title} has been edited")

    def delete_message(self, user, msg_no):
        usr = self.get_user_by_msgNo(msg_no)
        self.messages.pop((msg_no, usr))
        temp = {}
        for n, u in self.messages:
            if type(n) == str:
                temp[(n, u)] = self.messages[(n, u)]
            elif n > msg_no:
                temp[(n-1, u)] = self.messages[(n, u)]
            else:
                temp[(n, u)] = self.messages[(n, u)]

        self.messages = temp
        self.curr_msgNo -= 1
        self.write_to_file()
        print(f"Message {msg_no} in Thread {self.title} has been deleted")
        
    def get_user_by_msgNo(self, msg_no):
        for n, user in self.messages:
            if type(n) == str: continue
            if n == msg_no:
                return user

    def contains_msgNo(self, msg_no):
        if msg_no < 1 or msg_no >= self.curr_msgNo:
            return False
        else:
            return True

    def does_file_exist(self, fname):
        if fname in self.files:
            return True
        else:
            return False
    
    def write_to_file(self):
        with open(self.title, 'w') as f:
            f.write(f"Started by: {self.creator}")
            for n, usr in self.messages:
                if type(n) == str:
                    f.write(f"\n{usr} uploaded {self.messages[(n, usr)]}")
                else:
                    f.write(f"\n{n} {usr}: {self.messages[(n, usr)]}")
    
    def send_file(self, client, fname):
        with open(self.title + '-' + fname, 'rb') as f:
            upload = f.read()
            client.sendall(upload)
            print(f"{fname} downloaded from Thread {self.title}")
    
    def get_file_size(self, fname):
        return os.path.getsize(self.title + '-' + fname)
