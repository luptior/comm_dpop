from time import sleep

from rudp import *
from random import randint

from rudp.rudp2 import *

da = ('127.0.0.1', RCV_PORT)
s = []
strHead =[]

for i in range(1):
	s.append( rudpSocket(SDR_PORT - 9 + i) )
	strHead.append('s'+str(i)+':')

for i in range(50):
	try:
		r = 0
		s[r].sendto(strHead[r] + str(i), da , True)
		sleep(0.05)
	except MAX_RESND_FAIL:
		sleep(10)
		del s[r]
		break
sleep(10000)