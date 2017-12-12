#!/bin/bash
import sys, socket, socketserver, threading, os, re
import queue




class ThreadPoolMixIn(SocketServer.ThreadingMixIn):

    pool_size = 10 #No. of threads in the pool
    current_dir = DFS_ROOT_DIR
    servers = {}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #Connect to first file server and pass its directory
    address = ("0.0.0.0", 2049)
    s.connect(address)
    data = s.recv(512)
    print (data)
    #Connect to second file server and pass its directory
    address2 = ("0.0.0.0", 2050)
    s2.connect(address2)
    data = s2.recv(512)
    print (data)
    
    socketToSend = s

    """
    =========================================================
                THREAD INITIALIZATION FUNCTIONS
    =========================================================
    """
    #Main server loop
    def serve_forever(self):
        #Create the request queue
        self.request_queue = Queue.Queue(self.pool_size)
        for t in range(self.pool_size):
            t = threading.Thread(target = self.process_request_thread) #Initialize threads
            #print "Starting pool thread ", t.name
            t.start()

        while 1:
            self.handle_request() #Get the ball rolling

    #Start handling the requests sent to the server
    def handle_request(self):
        #requests are esentially socket objects
        request, client_address = self.get_request()
        #Place in the queue
        self.request_queue.put((request,client_address))

    #Get a request from the queue
    def process_request_thread(self):
        while 1:
            #ThreadingMixIn.process_request_thread(self, self.request_queue.get())
            try:
                request, client_address = self.request_queue.get()
            except Queue.Empty:
                pass
            #Fufill request
            self.finish_request(request, client_address)

    def resolve_socket(self, path):
          #path = os.path.expanduser(path)
          while path not in self.servers:
            #Go up one directory
            path = os.path.dirname(os.path.normpath(path))
          
          self.socketToSend = self.servers[path]
          
    

    def change_dir(self, path):
        #if path == os.pardir:
        if path == "..":
            self.current_dir = os.path.dirname(os.path.normpath(self.current_dir))
        elif os.path.exists(path):
            self.current_dir += path

        if not self.current_dir.endswith('/'):
                self.current_dir += '/'
        else:
            return -1
        
        self.resolve_socket(self.current_dir)
        return self.current_dir

    def list_dir(self, path):
        path = os.path.expanduser(path)
        lst = os.listdir(path)
        dirlst = ""
        for i in lst:
            dirlst += i + '\n'

        return dirlst





    def shutdown(self):
        server.server_close()
        #Force shutdown
        os._exit(os.EX_OK)


class ThreadedRequestHandler(SocketServer.BaseRequestHandler):
    pass

    #Open a thread for each client and handle requests
    """
    def handle(self):
        data = self.request.recv(1024)
        curr_thread = threading.current_thread()
        response = "{} - {}".format(curr_thread.name, data)
        self.request.sendall(response)
    """

class Server(ThreadPoolMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":

    HOST = "0.0.0.0"
    PORT = int(sys.argv[1])
    server = Server((HOST, PORT), ThreadedRequestHandler)
    print ("Server started - ", HOST, PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
