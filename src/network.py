"""
Size and calculation:

for ndarray

title = 96
every single element is 8 byte
every additional dimension is 16 byte


"""

import numpy as np
from time import sleep
import sys

# some constants for network communication

Q = 0.01
RTT = 100.  # unit in ms
MAX_SEG = 1460.  # unit in bytes


def throughput(q, rtt, s) -> float:
    # return unit in bytes / s
    return 1.22 * s / (rtt & np.sqrt(q)) * 1000


tp = throughput(Q, RTT, MAX_SEG)


def tran_time(size):
    # return 0.1 + size / 100 , return unit in s
    return size / throughput


def loss(s):
    # return a loss rate based on size
    return 1. / (1. + 1. / (s / 10. ** 3))


def divide_sleep(size):
    if np.random.ranf() >= loss(size):
        # successfully transmitted
        sleep(tran_time(size))
    else:
        # divide and send, timeout 10s
        sleep(5)
        divide_sleep(size / 2)
        divide_sleep(size / 2)


def proactive(size):
    # given a know relationship between size and expectation of delivery time
    # precalculated the function argmin = 7.9 ,so take 8 here
    if size <= 8:
        while np.random.ranf() < loss(size):
            sleep(5)
        else:
            sleep(tran_time(size))
    else:
        num = size / 8
        last = size % 8
        for i in range(num):
            # for the packages of size 8
            while np.random.ranf() < loss(8):
                sleep(5)
            else:
                sleep(tran_time(8))
        # for the last package
        if last != 0:
            while np.random.ranf() < loss(last):
                sleep(5)
            else:
                sleep(tran_time(last))



