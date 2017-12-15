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


#Initiating Thred Pool

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


class Client:
    # Initialise a new File System client
    def __init__(self, id, socket, path_to_root):
        self.id = id
        self.socket = socket
        self.dir_level = 0
        # Path to root is the path to the root of the file_system
        self.dir_path = [path_to_root]

    #
    # Functions for working with directories
    #

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

    #
    # Testing functions
    #
    def log_member_data(self):
        print ("")
        print ("dir_path: " + (self.dir_path).__repr__())
        print ("socket: " + (self.socket).__repr__())
        print ("id: %d" % self.id)
        print ("dir_level: %d" % self.dir_level)
        print ("")

class Locker:

    # List for storing active clients
    active_clients = []

    # Next ID to be assigned to new client and events
    clientId = 0
    eventId = 0

    # List of events and IDs
    # ( event_id , command, time )
    events = []

    # List of the paths of currently locked files
    # ( client_id, time, path )
    locked_files = []

    # ThreadPool will contain threads managing the autorelease
    # of locks
    Locker_threadpool = ThreadPool(1)

    # Create new File System Manager and initialise the root
    def __init__(self, root_path):
        self.root_path = root_path
        #Add autorelease function to a new thread
        self.Locker_threadpool.add_task(
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

    #
    # Functions for interacting with clients
    #

    # Adds a new client to the file system manager
    # Returns the id of the client
    def add_client(self, connection):
        print(self.gen_client_id())
        new_client_id = self.gen_client_id();
        new_client = Client(new_client_id, connection, self.root_path)
        self.active_clients.append(new_client)
        return new_client_id

    def remove_client(self, client_in):
        i = 0
        for client in self.active_clients:
            if client.id == client_in.id:
                self.active_clients.pop(i)
            i = i + 1

    def get_active_client(self, client_id):
        for client in self.active_clients:
            if client.id == client_id:
                return client

    def update_client(self, client_in):
        i = 0
        for client in self.active_clients:
            if client.id == client_in.id:
                self.active_clients[i] = client_in
            i = i + 1

    # checks if a client exists which has the same id as the one passed in
    def client_exists(self, id_in):
        for client in self.active_clients:
            if ( client.id == id_in ):
                return True
        return False

    # disconnect client from server
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

    #
    # Functions for interacting with events
    #

    def add_event(self, command):
        new_event_id = self.gen_event_id()
        event_timestamp = datetime.datetime.now()
        new_event_record = (new_event_id, command, event_timestamp)
        self.events.append(new_event_record)
        print ("%d\t%s\t%s" % (new_event_record[0], new_event_record[2], new_event_record[1]))

    def log_events(self):
        print ("EID\tTIME\t\t\t\tCOMMAND")
        for event in self.events:
            print ("%d\t%s\t%s" % (event[0], event[2], event[1]))
#
    # Functions for interacting with locking
    #

    # Locks an item if it is not locked
    # Return 0 : Item was locked
    # Return 1 : Item was already locked
    # Return 2 : Item doesn't exist
    # Return 3 : Item is a directory
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
            print (item_name +"has been locked")
            return 0

    # Unlocks an item if it was locked
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

    # Checks if an item is locked
    # Return True : Item is locked
    # Returns False : Item is not locked
    def check_lock(self, client, item_name):
        file_path = self.resolve_path(client.id, item_name)
        for locked_file in self.locked_files:
            if locked_file[2] == file_path:
                return True
        return False

    # Traverses the list of locked items and releases locked item if
    # client does not exist
    # Run in a thread initialized in the __init__ function
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

    def log_locks(self):
        print ("LID\tTIME\t\t\t\tPATH")
        for locked_file in self.locked_files:
            print ("%d\t%s\t%s" % locked_file)

