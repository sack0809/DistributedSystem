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
    

    
    def serverRun(this):
        this.request_queue = queue.Queue(this.pool_size)
        for trd in range(this.pool_size):
            trd = threading.Thread(target = this.process_request_thread) 
            trd.start()

        while 1:
            this.requestHandler() 

    
    def requestHandler(this):
        request, client_address = this.get_request()
        this.request_queue.put((request,client_address))

   
    def process_request_thread(this):
        while 1:
            try:
                request, client_address = this.request_queue.get()
            except queue.Empty:
                pass
                this.finish_request(request, client_address)



    

    def shutdown(this):
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
