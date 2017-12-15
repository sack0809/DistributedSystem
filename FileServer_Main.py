#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import sys
IS_PY2 = sys.version_info < (3, 0)
if IS_PY2:
    from Queue import Queue
else:
    from queue import Queue

from threading import Thread
import socket
import os
import FileServer

port_number = 9090

#ip_address = sockServeret.gethostbyname(sockServeret.gethostname())

fileManager = FileServer.FileSystemManager('FileSystemDir')



#Initiating Worker Thread


class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()
#Initiating Thread Pool

class ThreadPool:
    """ Pool of threads consuming tasks from a queue """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()

server_thread_pool = ThreadPool(100)

#Creating Server Socket and Accepting Client Connection

def createServerSocket():
    sockServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('127.0.0.1', port_number)
    print ("starting up on %s port %s" % server_address)
    sockServer.bind(server_address)
    sockServer.listen(1)

    while True:
        conn, client_address = sockServer.accept()
        print ("Connection from '{0}', '{1}'".format  ( conn, client_address))
        server_thread_pool.add_task(
            clientResponse,
            conn,
            client_address
        )

#Processing Client Response

def clientResponse(conn, client_address):
    try:
        #A client id is generated, that is associated with this client
        client_id = fileManager.add_client(conn)
        while True:
            data = conn.recv(2048).decode()
            print(str(data))
            split_data = seperate_input_data(data)
            # Respond to the appropriate message
            if data == "KILL_SERVICE":
                kill_service(conn)
            elif split_data[0] == "list":
                listFiles(conn, client_id, split_data)
            elif split_data[0] == "read":
                readFile(conn, split_data, client_id)
            elif split_data[0] == "write":
                writeFile(conn, split_data, client_id)
            elif split_data[0] == "delete":
                delete(conn, split_data, client_id)
            elif split_data[0] == "wd":
                workingDirectory(conn, split_data, client_id)
            elif split_data[0] == "exit":
                exit(conn, split_data, client_id)
            elif split_data[0] == "create":
                createFile(conn, split_data, client_id)
            #else:
             #   error_response(conn, 1)
    except:
        error_response(conn, 0)
        print ("Got error"+ split_data)
        conn.close()

#For shutting down the service

def kill_service(conn):
    # Kill service
    response = "Killing Service"
    conn.sendall("%s" % response)
    conn.close()
    os._exit(0)

#Listing all the files in the directory

def listFiles(conn, client_id, split_data):
    response = ""
    print (split_data)
    if len(split_data) == 1:
        print ("I am sending to fs")
        response = fileManager.list_directory_contents(client_id)
        conn.sendall(response)
    elif len(split_data) == 2:
        response = fileManager.list_directory_contents(client_id, split_data[1])
        conn.sendall(response)
    else:
        error_response(conn, 1)

#Reading the files from directory

def readFile(conn, split_data, client_id):
    if len(split_data) == 2:
        response = fileManager.read_item(client_id, split_data[1])
        conn.sendall(response)
    else:
        error_response(conn, 1)

#Writing into the File

def writeFile(conn, split_data, client_id):
    response = ""
    if len(split_data) == 2:
        res = fileManager.write_item(client_id, split_data[1], "")
        if res == 0:
            response = "write successfull"
        
        elif res == 2:
            response = "cannot write to a directory file"
        conn.sendall(response)
    elif len(split_data) == 3:
        res = fileManager.write_item(client_id, split_data[1], split_data[2])
        if res == 0:
            response = "write successfull"
        
        elif res == 2:
            response = "cannot write to a directory file"
        conn.sendall(response)
    else:
        error_response(conn, 1)

#Deleting the file from directory

def delete(conn, split_data, client_id):
    if len(split_data) == 2:
        res = fileManager.delete_file(client_id, split_data[1])
        response = ""
        if res == 0:
            response = "delete successfull"
        
        elif res == 2:
            response = "use rmdir to delete a directory"
        elif res == 3:
            response = "file doesn't exist"
        conn.sendall(response)
    else:
        error_response(conn, 1)

#Getting information of Working Directory

def workingDirectory(conn, split_data, client_id):
    if len(split_data) == 1:
        response = fileManager.get_working_dir(client_id)
        conn.sendall(response)
    else:
        error_response(conn, 1)

#Creating new file in the directory

def createFile(conn, split_data, client_id):
    if len(split_data) == 2:
        res = fileManager.create_file(client_id, split_data[1])
        response = ""
        if res == 0:
            response = "File Created Successfully"
        conn.sendall(response)
    else:
        error_response(conn, 1)

#Exit from the Server

def exit(conn, split_data, client_id):
    if len(split_data) == 1:
        fileManager.disconnect_client(conn, client_id)
    else:
        error_response(conn, 1)

#Error responses to Client

def error_response(conn, error_code):
    response = ""
    if error_code == 0:
        response = "server error"
    if error_code == 1:
        response = "no  command"
    conn.sendall(response)

#Processing the input data

def seperate_input_data(input_data):
    seperated_data = input_data.split('////')
    return seperated_data

if __name__ == '__main__':
    createServerSocket()
    # wait for threads to complete
    server_thread_pool.wait_completion()
