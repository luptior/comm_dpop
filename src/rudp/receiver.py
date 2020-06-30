from rudp import *
from random import randint
from rudp.rudp2 import *

da = ('127.0.0.1', SDR_PORT)

r = rudpSocket(RCV_PORT)
strHead = 'r:'

while True:
	print(r.recvfrom())
	sleep()