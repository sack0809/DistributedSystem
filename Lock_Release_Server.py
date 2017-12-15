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
import Locker
import FileServer
port_number = 9091

#ip_address = sockServeret.gethostbyname(sockServeret.gethostname())

#LockRelease = Locker.Locker('FileSystemDir')
LockRelease= FileServer.FileSystemManager('FileSystemDir')


#Initiating Thread Pool


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

def createServerSocket():
    # create sockServeret  and initialise to localhost:8000
    sockServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('127.0.0.1', port_number)
    print ("starting up on %s port %s" % server_address)
    # bind sockServeret to server address and wait for incoming connections4
    sockServer.bind(server_address)
    sockServer.listen(1)

    while True:
        # sockServer.accept returns a 2 element tuple
        connection, client_address = sockServer.accept()
        print(connection)
        print ("Connection from '{0}', '{1}'".format  ( connection, client_address))
        # Hand the client interaction off to a seperate thread
        print(connection)
        server_thread_pool.add_task(
            start_client_interaction,
            connection,
            client_address
        )


def start_client_interaction(connection, client_address):
    try:
        #A client id is generated, that is associated with this client
        client_id = LockRelease.add_client(connection)
        while True:
            data = connection.recv(2048).decode()
            print(str(data))
            split_data = seperate_input_data(data)
            #print (split_data[0])
            #print (split_data[1])
            # Respond to the appropriate message
            if data == "KILL_SERVICE":
                kill_service(connection)
            elif split_data[0] == "lock":
                print (split_data)
                lock(connection, split_data, client_id)
            elif split_data[0] == "release":
                release(connection, split_data, client_id)
            else:
                error_response(connection, 1)
    except:
        error_response(connection, 0)
        print ("Got error"+ split_data)
        connection.close()

def kill_service(connection):
    # Kill service
    response = "Killing Service"
    connection.sendall("%s" % response)
    connection.close()
    os._exit(0)

def lock(connection, split_data, client_id):
    if len(split_data) == 2:
        print (client_id)
        client = LockRelease.get_active_client(client_id)
        print ("Passing to Manager")
        print (client)
        print (split_data[1])
        res = LockRelease.lock_item(client, split_data[1])
        print (res)
        print ("File has been locked")
        response = ""
        if res == 0:
            response = "file locked"
        elif res == 1:
            response = "file already locked"
        elif res == 2:
            response = "file doesn't exist"
        elif res == 3:
            response = "locking directories is not supported"
        print (connection)
        print (type(response))
        connection.sendall(response)
    else:
        error_response(connection, 1)

def release(connection, split_data, client_id):
    if len(split_data) == 2:
        client = LockRelease.get_active_client(client_id)
        res = LockRelease.release_item(client, split_data[1])
        if res == 0:
            response = split_data[1] + " released"
        elif res == -1:
            response = "you do not hold the lock for %s" % split_data[1]
        connection.sendall(response)
    else:
        error_response(connection, 1)


def exit(connection, split_data, client_id):
    if len(split_data) == 1:
        LockRelease.disconnect_client(connection, client_id)
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
    createServerSocket()
    # wait for threads to complete
    server_thread_pool.wait_completion()


