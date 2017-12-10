import sys
import socketserver
import threading
try:
    import queue
except ImportError:
    import Queue as queue
#from cache import Cache
#from locker import Locker

dir= "~/test-dir/"
initialized = False

class ThreadPoolMixIn(socketserver.ThreadingMixIn):

    pool_size = 10 #No. of threads in the pool
    current_dir = dir
    initialized = False
    root_dir = None
    

    
    def serverRun(self):
        self.request_queue = queue.Queue(self.pool_size)
        for trd in range(self.pool_size):
            trd = threading.Thread(target = self.process_request_thread) 
            trd.start()

        while 1:
            self.requestHandler() 

    
    def requestHandler(self):
        request, client_address = self.get_request()
        self.request_queue.put((request,client_address))

   
    def process_request_thread(self):
        while 1:
            try:
                request, client_address = self.request_queue.get()
            except queue.Empty:
                pass
                self.finish_request(request, client_address)



    

    def shutdown(self):
        server.server_close()
         

class ThreadedRequestHandler(socketserver.BaseRequestHandler):
    pass

class FileServer(ThreadPoolMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":

    HOST = "0.0.0.0"
    PORT = int(sys.argv[1])
    server = FileServer((HOST, PORT), ThreadedRequestHandler)
    print  ("File Server started - ", HOST, PORT)
    try:
        server.serverRun()
    except KeyboardInterrupt:
        server.shutdown()
