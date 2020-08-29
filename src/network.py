"""
Size and calculation:

for ndarray

title = 96
every single element is 8 byte
every additional dimension is 16 byte


"""

import numpy as np
from numpy import double
from scipy.special import comb, perm
from time import sleep
import socket
from contextlib import closing


# a function to find free port on local host
def find_free_port(ip='localhost'):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((ip, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


# some constants for network communication
MAX_SEG = 1460.  # TCP maximum segment size


def tcp_throughput(q, rtt, s) -> float:
    # return unit in bytes / s
    # function generated from mathis equation
    return 1.22 * s / (rtt * np.sqrt(q))


def udp_throughput(q, rtt, s) -> float:
    # TODO
    raise NotImplementedError("udp_throughput not implemented")


def tran_time(agent, size):
    # return 0.1 + size / 100 , return unit in s
    if "TCP" in agent.network_protocol:
        return size / tcp_throughput(agent.drop, agent.rtt, MAX_SEG)
    elif "UDP" in agent.network_protocol:
        if size < agent.buffer_size:
            return agent.rtt
        else:
            agent.logger.error(f"Not implemented")
            raise OverflowError(f"{size} is lager than buffer size {agent.buffer_size}")


def tcp_time_ber(ber: float, bitlength: int) -> float:
    # TODO:
    # to simulate the time spent for tcp with a certain percentage of ber The TCP checksum is two bytes long Traces
    # of Internet packets from the past two years show that between 1 packet in 1,100 and 1 packet in 32,000
    # fails the TCP checksum
    # if float(ber) == 0:
    #     return 0
    # else:
    #     return 0

    raise NotImplementedError("tcp_time_ber not implemented")


def rs_rej_prop(msg_len: int, rs_k: int, ber: float) -> float:
    """
    calculate the possibility that a rs coded string to be unrecoverable
    :param msg_len: the length of the total message
    :param rs_k: int, the k value of RS code
    :param ber: float, bit error rate
    :return: probability that the message get rejected
    """
    result = sum([comb(msg_len, k) * ber ** k * (1 - ber) ** (msg_len - k) for k in range(0, rs_k + 1)])
    if result > 1:
        return 0
    else:
        return 1 - result


def checksum_rej_prop(msg_len: int, ber: float) -> float:
    """ a function that the package will get rejected by TCP checksum
    :param msg_len: the length of the total message
    :param ber: bit error rate
    :return: a float of possibility it get rejected
    """
    return 1 - (1 - ber) ** msg_len

# def loss(s):
#     # return a loss rate based on size
#     return 1. / (1. + 1. / (s / 10. ** 3))
#
#
# def divide_sleep(size):
#     if np.random.ranf() >= loss(size):
#         # successfully transmitted
#         sleep(tran_time(size))
#     else:
#         # divide and send, timeout 10s
#         sleep(5)
#         divide_sleep(size / 2)
#         divide_sleep(size / 2)
#
#
# def proactive(size):
#     # given a know relationship between size and expectation of delivery time
#     # precalculated the function argmin = 7.9 ,so take 8 here
#     if size <= 8:
#         while np.random.ranf() < loss(size):
#             sleep(5)
#         else:
#             sleep(tran_time(size))
#     else:
#         num = size / 8
#         last = size % 8
#         for i in range(num):
#             # for the packages of size 8
#             while np.random.ranf() < loss(8):
#                 sleep(5)
#             else:
#                 sleep(tran_time(8))
#         # for the last package
#         if last != 0:
#             while np.random.ranf() < loss(last):
#                 sleep(5)
#             else:
#                 sleep(tran_time(last))
