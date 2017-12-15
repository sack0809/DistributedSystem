#!/usr/bin/python2.7

import sys
IS_PY2 = sys.version_info < (3, 0)
import datetime
import time
import os
import shutil



if IS_PY2:
    from Queue import Queue
else:
    from queue import Queue

from threading import Thread


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

#Information about Client

class Client:
    def __init__(self, id, socket, path_to_root):
        self.id = id
        self.socket = socket
        self.dir_level = 0
        self.dir_path = [path_to_root]
  
    
   # Move into the passed directory
   
    def change_directory(self, dir_name ):
        self.dir_level = self.dir_level + 1
        self.dir_path.append( dir_name )

    # Move up a directory level
    # Return 0 : Success
    # Return 1 : At top directory level
   
    def move_up_directory(self):
        
        if self.dir_level > 0:
           self.dir_path.pop()
           self.dir_level = self.dir_level - 1
           return 0
        else:
           return 1

# Processing of File

class FileSystemManager:

    active_clients = []

    clientId = 0
    eventId = 0

    events = []

    locked_files = []

    file_system_manager_threadpool = ThreadPool(1)

    def __init__(self, root_path):
        self.root_path = root_path
        #Add autorelease function to a new thread
        self.file_system_manager_threadpool.add_task(
            self.auto_release
        )

    # Generate a client ID and update clientId
    def gen_client_id(self):
        return_client_id = self.clientId
        self.clientId = self.clientId + 1
        return return_client_id

    # Generate a client ID and update eventId
    
    def gen_event_id(self):
        return_event_id = self.eventId
        self.eventId = self.eventId + 1
        return return_event_id

   #Adding Client

    def add_client(self, connection):
        print(self.gen_client_id())
        new_client_id = self.gen_client_id();
        new_client = Client(new_client_id, connection, self.root_path)
        self.active_clients.append(new_client)
        return new_client_id

   #Removing Client

    def remove_client(self, client_in):
        i = 0
        for client in self.active_clients:
            if client.id == client_in.id:
                self.active_clients.pop(i)
            i = i + 1

   #Information about active clients

    def get_active_client(self, client_id):
        for client in self.active_clients:
            if client.id == client_id:
                return client

   #Update Client id

    def update_client(self, client_in):
        i = 0
        for client in self.active_clients:
            if client.id == client_in.id:
                self.active_clients[i] = client_in
            i = i + 1

    #Checking Client Existence

    def client_exists(self, id_in):
        for client in self.active_clients:
            if ( client.id == id_in ):
                return True
        return False

    #Disconnecting Client

    def disconnect_client(connection, client_id):
        # get client
        client = self.get_active_client(client_id)
        # remove client from active clients
        self.remove_client(client)
        # disconnect socket
        connection.sendall("disconnected")
        connection.close()
        # add event
        self.add_event("disconnect client %d" % client_id)

    #Adding Corresponding Event

    def add_event(self, command):
        new_event_id = self.gen_event_id()
        event_timestamp = datetime.datetime.now()
        new_event_record = (new_event_id, command, event_timestamp)
        self.events.append(new_event_record)
        print ("%d\t%s\t%s" % (new_event_record[0], new_event_record[2], new_event_record[1]))

    #Generating Logs

    def log_events(self):
        print ("EID\tTIME\t\t\t\tCOMMAND")
        for event in self.events:
            print ("%d\t%s\t%s" % (event[0], event[2], event[1]))

    #Listing Files
  
    def list_directory_contents(self, client_id, item_name = ""):
        path = self.resolve_path(client_id, item_name)
        item_type = self.item_exists(client_id, item_name)
        if item_type == -1:
            return "No such directory %s" % item_name
        elif item_type == 0:
            return "Cannot list contents of %s" % item_name
        else:
            item_list = os.listdir("./" + path)
            return_string = "Type\tPath"
            for item in item_list:
                list_item_type = self.item_exists(client_id, item)
                if list_item_type == 0:
                    return_string = return_string + "\n" + "f\t" + item
                elif list_item_type == 1:
                    return_string = return_string + "\n" + "d\t" + item
            return return_string

    def resolve_path(self, client_id, item_name):
        client = self.get_active_client(client_id)
        file_path = ""
        for path_element in client.dir_path:
            file_path = file_path + "%s/" % path_element
        file_path = file_path + item_name
        return file_path

   #Information about current directory  
 
    def get_working_dir(self, client_id):
        client = self.get_active_client(client_id)
        file_path = ""
        for path_element in client.dir_path:
            file_path = file_path + "%s/" % path_element
        return file_path

   #Locking File

    def lock_item(self, client, item_name):
        print ("In Locking")
        file_path = self.resolve_path(client.id, item_name)
        # if item is not a file or doesnt exist exit
        print (file_path)
        item_type = self.item_exists(client.id, item_name)
        if item_type == -1:
            return 2
        elif item_type == 1:
            return 3
        if self.check_lock(client, item_name) ==  True:
            return 1
        else:
            lock_timestamp = datetime.datetime.now()
            lock_record = (client.id, lock_timestamp, file_path)
            self.locked_files.append(lock_record)
            self.add_event("lock " + file_path)
            return 0
    #Release File

    def release_item(self, client, item_name):
        file_path = self.resolve_path(client.id, item_name)
        i = 0
        item_released = False
        for locked_file in self.locked_files:
            if file_path == locked_file[2]:
                if client.id == locked_file[0]:
                    self.locked_files.pop(i)
                    self.add_event("release " + file_path)
                    item_released = True
            i = i + 1
        if item_released:
            return 0
        else:
            return -1
    
    #Check Lock
    
    def check_lock(self, client, item_name):
        file_path = self.resolve_path(client.id, item_name)
        for locked_file in self.locked_files:
            if locked_file[2] == file_path:
                return True
        return False

   #Auto Release

    def auto_release(self):
        while True:
            # auto release occurs every minute
            time.sleep(60)
            new_locked_file_list = []
            for locked_file in self.locked_files:
                for client in self.active_clients:
                    if locked_file[0] == client.id:
                        new_locked_file_list.append(locked_file)
            self.locked_files = new_locked_file_list
            self.add_event("lock auto-release")

   #Generating logs

    def log_locks(self):
        print ("LID\tTIME\t\t\t\tPATH")
        for locked_file in self.locked_files:
            print ("%d\t%s\t%s" % locked_file)

   #Checking File

    def item_exists(self, client_id, item_name):
        file_path = self.resolve_path(client_id, item_name)
        is_file = os.path.isfile("./"+file_path)
        if is_file == True:
            return 0
        is_dir = os.path.isdir("./"+file_path)
        if is_dir == True:
            return 1
        else:
            return -1
 
  #Reading File 
  
    def read_item(self, client_id, item_name):
        # check if item exists
        item_type = self.item_exists(client_id, item_name)
        if item_type == -1:
            return "%s doesn't exist" % item_name
        elif item_type == 1:
            return "%s is a directory" % item_name
        elif item_type == 0:
            # read item
            file_path = self.resolve_path(client_id, item_name)
            file = open(file_path, 'r')
            file_contents = file.read()
            # add event
            self.add_event("read " + file_path)
            return_string = "%s////%s" % (file_path, file_contents)
            return return_string
 
  #Writing File

    def write_item(self, client_id, item_name, file_contents):
        item_type = self.item_exists(client_id, item_name)
        # exit if the item is a directory
        if item_type == 1:
            return 2
        # lock_item
        client = self.get_active_client(client_id)
        lock_res = self.lock_item(client, item_name)
        # Exit if file is locked
        if lock_res == 1:
            return 1
        # write to it
        file_path = self.resolve_path(client_id, item_name)
        file = open(file_path, 'w+')
        file.truncate()
        file.write(file_contents)
        # add write event
        self.add_event("write " + file_path)
        # If item had previously never existed
        if lock_res == 2:
            return 0
        # release it
        self.release_item(client, item_name)
        return 0
  
 #Delete File
    
    def delete_file(self, client_id, item_name):
        item_type = self.item_exists(client_id, item_name)
        # exit if the item does not exist
        if item_type == -1:
            return 3
        # exit if the item is a directory
        if item_type == 1:
            return 2
        # lock_item
        client = self.get_active_client(client_id)
        lock_res = self.lock_item(client, item_name)
        # Exit if file is locked
        if lock_res == 1:
            return 1
        # delete file
        file_path = self.resolve_path(client_id, item_name)
        os.remove(file_path)
        # add delete event
        self.add_event("delete " + file_path)
        # release it
        self.release_item(client, item_name)
        return 0
 
#Create File 
   
    def create_file(self, client_id, item_name):
        item_type = self.item_exists(client_id, item_name)
        #path = self.resolve_path(client_id, directory_name)        
        # exit if the item does not existi
        #print (path)
        if os.path.exists(item_name):
           os.utime(item_name, None)
        else:
           open(item_name, 'a').close()   
           self.add_event("Created File" + item_name)
           #self.release_item(client, item_name)
           return 0

