"""
server reads file and send to client

"""

import datetime
import hashlib
import pickle
import socket
import threading
import time
import numpy as np


# Packet class definition
class packet():
    checksum = 0
    length = 0
    seqNo = 0
    msg = 0

    def make(self, data):
        if isinstance(data, bytes):
            self.msg = data
            self.length = str(len(data))
            self.checksum = hashlib.sha1(self.msg).hexdigest()
            print(f"Length: {self.length}\nSequence number: {self.seqNo}")
        elif isinstance(data, str):
            self.msg = pickle.dumps(data)
            self.length = str(len(data))
            self.checksum = hashlib.sha1(self.msg).hexdigest()
            print(f"Length: {self.length}\nSequence number: {self.seqNo}")

    def serialize(self) -> str:
        serialized_packet = str(self.checksum) + delimiter + \
                            str(self.seqNo) + delimiter + \
                            str(self.length) + delimiter + \
                            str(self.msg)
        return serialized_packet


# Connection handler
def handleConnection(addr, ):
    drop_count = 0
    packet_count = 0
    fragment_size = 500
    time.sleep(0.5)
    if lossSimualation:
        packet_loss_percentage = float(input("Set PLP (0-99)%: ")) / 100.0
        while packet_loss_percentage < 0 or packet_loss_percentage >= 1:
            packet_loss_percentage = float(input("Enter a valid PLP value. Set PLP (0-99)%: ")) / 100.0
    else:
        packet_loss_percentage = 0
    start_time = time.time()
    print("Request started at: " + str(datetime.datetime.utcnow()))
    pkt = packet()
    threadSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    data = np.random.randint(100, size=[3, 4, 5])
    data = pickle.dumps(data)

    # Fragment and send file fragment_size byte
    x = 0
    while x < int(len(data) / fragment_size) + 1:
        print(f"Sending package {x}")
        packet_count += 1
        randomised_plp = np.random.random()
        if packet_loss_percentage < randomised_plp:

            # extract the partial dat to be msg
            msg = data[x * fragment_size: (x + 1) * fragment_size]
            pkt.make(msg)
            serialized_pkt = pickle.dumps(pkt.serialize())

            # Send packet
            sent = threadSock.sendto(serialized_pkt, addr)
            print(f'Sent {sent} bytes back to {addr}, awaiting acknowledgment..')
            threadSock.settimeout(10)

            # Wait for Ack
            try:
                ack, addr = threadSock.recvfrom(100)
                ack = pickle.loads(ack)
            except:
                print("Time out reached, resending ...%s" % x)
                continue
            if ack.split(",")[0] == str(pkt.seqNo):
                pkt.seqNo = int(not pkt.seqNo)
                print(f"Acknowledged by: {ack} ")
                x += 1
        else:
            print("Dropped packet\n")
            drop_count += 1

    print(f"Packets served: {packet_count}")

    if lossSimualation:
        print(f"Dropped packets:  {str(drop_count)} "
              f"\nComputed drop rate: {float(drop_count) / float(packet_count) * 100.0}")

    print("Sending finished.")


if __name__ == '__main__':
    # PLP Simulation settings
    lossSimualation = False

    # Set addr and port
    serverAddress = "localhost"
    serverPort = 8233

    # Delimiter
    delimiter = "|:|:|"

    # Seq number flag
    seqFlag = 0

    # Start - Connection initiation
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = (serverAddress, serverPort)
    print('Starting up on %s port %s' % server_address)
    sock.bind(server_address)

    # Listening for requests indefinitely

    print('Waiting to receive message')
    pdata, address = sock.recvfrom(600)
    connectionThread = threading.Thread(target=handleConnection, args=(address,))
    connectionThread.start()
    print('Received %s bytes from %s' % (len(pdata), address))
