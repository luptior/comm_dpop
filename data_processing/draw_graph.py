import numpy as np
import matplotlib.pyplot as plt

import network


def draw_throughput():
    Q = 0.01
    RTT = 0.1  # unit in s
    MAX_SEG = 1460.  # unit in bytes

    x = np.arange(100, 50000)
    speed = 10**6


    size = 1000

    y_tcp = [size/network.tcp_throughput(q=Q, rtt=RTT, s=MAX_SEG) for size in x]
    y_udp = [size/network.udp_throughput(q=Q, rtt=RTT, s=MAX_SEG) for size in x]

    plt.plot(x, y_tcp, label="tcp")
    plt.plot(x, y_udp, label="udp")
    plt.legend()
    plt.show()


if __name__ == '__main__':
    draw_throughput()