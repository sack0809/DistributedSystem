#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 10 03:49:50 2017

@author: playsafe
"""

import sys, socket, struct, random

class Client():

	

	def __init__(self, port):

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(1.5)
		self.ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
		self.port = port
		s.connect(("0.0.0.0", self.port))

		valid = False

		while 1:

			while not valid:
				self.message = input(">: ")
				if any(x in self.message for x in self.commands):
					valid = True
				else:
					print ("Invalid Command\n")
			s.sendall(self.message)
			if self.message == "QUIT":
				sys.exit()
			try:
				recv_data = s.recv(4096)
				print (recv_data + '\n')
				valid = False;
			except socket.timeout:
				print ("Something went wrong\n")


if __name__ == '__main__':

	port = int(sys.argv[1])
	Client(port)
