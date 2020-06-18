"""
Size and calculation:

for ndarray

title = 96
every single element is 8 byte
every additional dimension is 16 byte


"""

import numpy as np
from time import sleep

# some constants for network communication

Q = 0.01
RTT = 100.  # unit in ms
MAX_SEG = 1460.  # unit in bytes


def throughput(agent, q, rtt, s) -> float:
    # return unit in bytes / s
    return 1.22 * s / (rtt * np.sqrt(q)) * agent.net_speed


def tran_time(agent, size):
    # return 0.1 + size / 100 , return unit in s
    return size / throughput(agent, Q, RTT, MAX_SEG)


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


def tcp_time_ber(ber: float, bitlength: int) -> float:
    # to simulate the time spent for tcp with a certain percentage of ber
    # The TCP checksum is two bytes long
    # Traces of Internet packets from the past two years show that between 1 packet in 1,100 and 1 packet in 32,000 fails the TCP checksum
    if float(ber) == 0:
        return 0
    else:
        return 0
