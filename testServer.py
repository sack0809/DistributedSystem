import socket
import sys
import threading


class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

# Create a TCP/IP socket
#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to the port
#server_name = sys.argv[1]


#server_address = (server_name, 10000)
#print (sys.stderr, 'starting up on %s self.port %s' % self.host)
#sock.bind(server_address)
#sock.listen(1)

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            threading.Thread(target = self.listenToClient,args = (client,address)).start()



    def listenToClient(self, client, address):
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    # Set the response to echo back the recieved data 
                    response = data
                    client.send(response)
                else:
                    raise error('Client disconnected')
            except:
                client.close()
                return False

if __name__ == "__main__":
    while True:
        port_num = input("Port? ")
        try:
            port_num = int(port_num)
            break
        except ValueError:
            pass

    ThreadedServer('',port_num).listen()


#while True:
    # Wait for a connection
  #  print (sys.stderr, 'waiting for a connection')
   # connection, client_address = sock.accept()
##try:
  ##      print (sys.stderr, 'connection from', client_address)

        # Receive the data in small chunks and retransmit it
    #    while True:
     #       data = connection.recv(16)
      #      print  (sys.stderr, 'received "%s"' % data)
       #     if data:
        #        print (sys.stderr, 'sending data back to the client')
         #       connection.sendall(data)
          #  else:
             #   print (sys.stderr, 'no more data from', client_address)
           #     break
            #
#finally:
        # Clean up the connection
 #       connection.close()
