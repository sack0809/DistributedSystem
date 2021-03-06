#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import sys
IS_PY2 = sys.version_info < (3, 0)
import socket
import time
import os
import io

if IS_PY2:
    from Queue import Queue
else:
    from queue import Queue

from threading import Thread
# this is a multithreaded client program that was used to test
# the server code

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

#Initiating ThreadPool

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



client_thread_pool = ThreadPool(5)

#ip_address = socket.gethostbyname(socket.gethostname())

port_num = 9090

#each 1 is 10 seconds
cache_time = 2

# Stores last 5 accessed items
# (file_path, file_contents, age)
cache_queue = []

response_var = ""

#Connecting to Server and Sending Message

def connectServer():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('127.0.0.1', port_num)
    print ("connecting to %s on port %s\n" % server_address)
    sock.connect(server_address)
    socktest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address_test = ('127.0.0.1', 9091)
    print ("connecting to %s on port %s\n" % server_address_test)
    socktest.connect(server_address_test)
    client_thread_pool.add_task(
        get_server_response,
        sock
    )
    client_thread_pool.add_task(
        get_server_response,
        socktest
    )

    client_thread_pool.add_task(
        auto_update_cache
    )
    client_thread_pool.add_task(
        auto_update_cache
    )

    while True:
        user_in = raw_input()
       # print("Given by user:"+user_in)
        #user_in =str.encode(user_in)
        message = generate_message(user_in)
       # print("Passed to method"+message)
        cache_res = cache_interaction(sock, message)
        # if there is no cached response
        if cache_res == None:
           if message.startswith("lock") or message.startswith("release"):
              socktest.send(message)
              print ("Message Sent"+message)
           else:
               sock.send(message)
               print ("Message Sent"+message)
           if message == "exit":
               os._exit(0)
        else:
            print (cache_res)

    sock.close()
    socktest.close()

#Processing Server Response

def get_server_response(socket):
    global response_var
    while True:
        data = socket.recv( 1024 )
        print (data)
        response_var = data
        if (data != None):
            # if reading cache item
            if(len(data.split("////")) == 2):
                split_data = data.split("////")
                add_to_cache(split_data[0], split_data[1])
                print (split_data[1])
            else:
                print (data)

#Processing Input Message

def generate_message(input):
    #print(input)
    split_input = input.split(" ")
    print (split_input)
    if split_input[0] == "write":
       # if len(split_input) != 2:
        #  print ("unrecognised command")
         # return ""
        print(split_input[1])
        print (split_input[2])
        try:
            #temp=split_input[1]
            #file = open (temp, 'w') 
            #print (file)
            #file_contents = file.read()
            with open(split_input[1], 'a') as inf:
          	 file_contents = inf.write(split_input[2])
                 #print(file_contents)
            return "%s////%s////%s" % (split_input[0], split_input[1], split_input[2])
        except IOError:
             print ("no such file in source directory")
             return ""
    else:
        return '////'.join(split_input)

#Cache Interaction

def cache_interaction(connection, message):
    global response_var
    split_message = message.split("////")
    if len(split_message) == 2 and split_message[0] == "read":
        connection.send("pwd")
        time.sleep(1)
        response_message = response_var
        search_term = "%s%s" % (response_message, split_message[1])
        return_message = search_cache(search_term)
        log_cache()
        print (search_term)
        return return_message
    return None

# searches the cache for an item
def search_cache(path):
    for item in cache_queue:
        if item[0] == path:
            return item[1]
    return None

# adds an item to the cache
def add_to_cache(path, contents):
    cache_queue.insert(0, (path, contents, 0))
    if len(cache_queue) > 5:
        cache_queue.pop()

# logs the contents of the cache
def log_cache():
    for item in cache_queue:
        print ("%s\t%s\t%d" % (item))

# function removes old items from cache
def auto_update_cache():
    global cache_queue
    while True:
        time.sleep(10)
        new_cache_queue = []
        for item in cache_queue:
            if item[2] < cache_time:
                new_cache_record = (item[0], item[1], item[2] + 1)
                new_cache_queue.append(new_cache_record)
        cache_queue = new_cache_queue

if __name__ == '__main__':
    # Main line for program
    # Create 20 tasks that send messages to the server
    connectServer()
    # wait for threads to complete before finishing program
    client_thread_pool.wait_completion()
