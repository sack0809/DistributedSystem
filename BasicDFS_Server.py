#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 23:25:35 2017

@author: playsafe
"""
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

#ip_address = socket.gethostbyname(socket.gethostname())

file_system_manager = FileServer.FileSystemManager('FileSystemDir')






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

def create_server_socket():
    # create socket  and initialise to localhost:8000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('127.0.0.1', port_number)
    print ("starting up on %s port %s" % server_address)
    # bind socket to server address and wait for incoming connections4
    sock.bind(server_address)
    sock.listen(1)

    while True:
        # sock.accept returns a 2 element tuple
        connection, client_address = sock.accept()
        print ("Connection from %s  \n" %   connection, client_address)
        # Hand the client interaction off to a seperate thread
        server_thread_pool.add_task(
            start_client_interaction,
            connection,
            client_address
        )


def start_client_interaction(connection, client_address):
    try:
        #A client id is generated, that is associated with this client
        client_id = file_system_manager.add_client(connection)
        while True:
            data = connection.recv(2048).decode()
            print(str(data))
            split_data = seperate_input_data(data)
            # Respond to the appropriate message
            if data == "KILL_SERVICE":
                kill_service(connection)
            elif split_data[0] == "ls":
                ls(connection, client_id, split_data)
            elif split_data[0] == "cd":
                cd(connection, split_data, client_id)
            elif split_data[0] == "up":
                up(connection, split_data, client_id)
            elif split_data[0] == "read":
                read(connection, split_data, client_id)
            elif split_data[0] == "write":
                write(connection, split_data, client_id)
            elif split_data[0] == "delete":
                delete(connection, split_data, client_id)
            elif split_data[0] == "mkdir":
                mkdir(connection, split_data, client_id)
            elif split_data[0] == "rmdir":
                rmdir(connection, split_data, client_id)
            elif split_data[0] == "pwd":
                pwd(connection, split_data, client_id)
            elif split_data[0] == "exit":
                exit(connection, split_data, client_id)
            else:
                error_response(connection, 1)
    except:
        error_response(connection, 0)
        connection.close()

def kill_service(connection):
    # Kill service
    response = "Killing Service"
    connection.sendall("%s" % response)
    connection.close()
    os._exit(0)

def ls(connection, client_id, split_data):
    response = ""
    if len(split_data) == 1:
        response = file_system_manager.list_directory_contents(client_id)
        connection.sendall(response)
    elif len(split_data) == 2:
        response = file_system_manager.list_directory_contents(client_id, split_data[1])
        connection.sendall(response)
    else:
        error_response(connection, 1)

def cd(connection, split_data, client_id):
    if len(split_data) == 2:
        res = file_system_manager.change_directory(split_data[1], client_id)
        response = ""
        if res  == 0:
            response = "changed directory to %s" % split_data[1]
        elif res == 1:
            response = "directory %s doesn't exist" % split_data[1]
        connection.sendall(response)
    else:
        error_response(connection, 1)

def up(connection, split_data, client_id):
    if len(split_data) == 1:
        file_system_manager.move_up_directory(client_id)
    else:
        error_response(connection, 1)

def read(connection, split_data, client_id):
    if len(split_data) == 2:
        response = file_system_manager.read_item(client_id, split_data[1])
        connection.sendall(response)
    else:
        error_response(connection, 1)

def write(connection, split_data, client_id):
    response = ""
    if len(split_data) == 2:
        res = file_system_manager.write_item(client_id, split_data[1], "")
        if res == 0:
            response = "write successfull"
        
        elif res == 2:
            response = "cannot write to a directory file"
        connection.sendall(response)
    elif len(split_data) == 3:
        res = file_system_manager.write_item(client_id, split_data[1], split_data[2])
        if res == 0:
            response = "write successfull"
        
        elif res == 2:
            response = "cannot write to a directory file"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def delete(connection, split_data, client_id):
    if len(split_data) == 2:
        res = file_system_manager.delete_file(client_id, split_data[1])
        response = ""
        if res == 0:
            response = "delete successfull"
        
        elif res == 2:
            response = "use rmdir to delete a directory"
        elif res == 3:
            response = "file doesn't exist"
        connection.sendall(response)
    else:
        error_response(connection, 1)



def mkdir(connection, split_data, client_id):
    if len(split_data) == 2:
        response = ""
        res = file_system_manager.make_directory(client_id, split_data[1])
        if res == 0:
            response = "new directory %s created" % split_data[1]
        elif res == 1:
            response = "file of same name exists"
        elif res == 2:
            response = "directory of same name exists"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def rmdir(connection, split_data, client_id):
    if len(split_data) == 2:
        response = ""
        res = file_system_manager.remove_directory(client_id, split_data[1])
        if res == -1:
            response = "%s doesn't exist" % split_data[1]
        elif res == 0:
            response = "%s removed" % split_data[1]
        elif res == 1:
            response = "%s is a file" % split_data[1]
        elif res == 2:
            response = "directory has locked contents"
        connection.sendall(response)
    else:
        error_response(connection, 1)

def pwd(connection, split_data, client_id):
    if len(split_data) == 1:
        response = file_system_manager.get_working_dir(client_id)
        connection.sendall(response)
    else:
        error_response(connection, 1)

def exit(connection, split_data, client_id):
    if len(split_data) == 1:
        file_system_manager.disconnect_client(connection, client_id)
    else:
        error_response(connection, 1)

def error_response(connection, error_code):
    response = ""
    if error_code == 0:
        response = "server error"
    if error_code == 1:
        response = "unrecognised command"
    connection.sendall(response)

#Function to split reveived data strings into its component elements
def seperate_input_data(input_data):
    seperated_data = input_data.split('////')
    return seperated_data

if __name__ == '__main__':
    create_server_socket()
    # wait for threads to complete
    server_thread_pool.wait_completion()
