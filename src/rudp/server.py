import pickle
import socket
import threading
import hashlib
import time
import datetime
import random

# Packet class definition
class packet():
    checksum = 0;
    length = 0;
    seqNo = 0;
    msg = 0;

    def make(self, data):
        self.msg = data
        self.length = str(len(data))
        self.checksum = hashlib.sha1(pickle.dumps(data)).hexdigest()
        print(f"Length: {self.length}\nSequence number: {self.seqNo}")


# Connection handler
def handleConnection(address, pdata):

    data = pickle.loads(pdata)
    drop_count = 0
    packet_count = 0
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
    # try:
        # Read requested file

    try:
        print("Opening file %s" % data)
        fileRead = open(data, 'r')
        data = fileRead.read()
        fileRead.close()
    except:
        msg = "FNF";
        pkt.make(msg);
        finalPacket = str(pkt.checksum) + delimiter + str(pkt.seqNo) + delimiter + str(
            pkt.length) + delimiter + pkt.msg
        threadSock.sendto(finalPacket, address)
        print("Requested file could not be found, replied with FNF")
        return

    # Fragment and send file 500 byte by 500 byte
    x = 0
    while x < (len(data) / 500) + 1:
        packet_count += 1
        randomised_plp = random.random()
        if packet_loss_percentage < randomised_plp:
            msg = data[x * 500:x * 500 + 500];
            pkt.make(msg);
            finalPacket = str(pkt.checksum) + delimiter + str(pkt.seqNo) + delimiter + str(
                pkt.length) + delimiter + pkt.msg

            finalPacket = pickle.dumps(finalPacket)
            # Send packet
            sent = threadSock.sendto(finalPacket, address)
            print(f'Sent {sent} bytes back to {address}, awaiting acknowledgment..')
            threadSock.settimeout(2)
            try:
                ack, address = threadSock.recvfrom(100);
            except:
                print("Time out reached, resending ...%s" % x);
                continue;
            if ack.split(",")[0] == str(pkt.seqNo):
                pkt.seqNo = int(not pkt.seqNo)
                print(f"Acknowledged by: {ack} "
                      f"\nAcknowledged at: { datetime.datetime.utcnow()} "
                      f"\nElapsed: {time.time() - start_time}")
                x += 1
        else:
            print("\n------------------------------\n\t\tDropped packet\n------------------------------\n")
            drop_count += 1
    print("Packets served: " + str(packet_count))
    if lossSimualation:
        print(f"Dropped packets:  {str(drop_count)} "
              f"\nComputed drop rate: {float(drop_count) / float(packet_count) * 100.0}" )
    # except:
    #     print("Internal server error")


if __name__ == '__main__':

    # PLP Simulation settings
    lossSimualation = False

    # Set address and port
    serverAddress = "localhost"
    serverPort = 10000

    # Delimiter
    delimiter = "|:|:|";

    # Seq number flag
    seqFlag = 0

    # Start - Connection initiation
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = (serverAddress, serverPort)
    print('Starting up on %s port %s' % server_address)
    sock.bind(server_address)

    # Listening for requests indefinitely
    while True:
        print('Waiting to receive message')
        pdata, address = sock.recvfrom(600)
        connectionThread = threading.Thread(target=handleConnection, args=(address, pdata))
        connectionThread.start()
        print('Received %s bytes from %s' % (len(pdata), address))
