"""
client request data

"""


import socket
import hashlib
import os
import pickle
import numpy as np


# Set address and port
serverAddress = "localhost"
serverPort = 8233

# Delimiter
delimiter = "|:|:|"

data_store = ""


if __name__ == '__main__':
    # Start - Connection initiation
    while 1:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10)
        server_address = (serverAddress, serverPort)
        # userInput = input("\nRequested file: ")
        # message = userInput

        messsage = np.random.randint(10, size=(2,3,4))

        seqNoFlag = 0

        try:
            # Connection trials
            connection_trials_count = 0
            # Send data
            print(f'Requesting')
            pdata = pickle.dumps("")
            sent = sock.sendto(pdata, server_address)
            # Receive indefinitely
            while 1:
                # Receive response
                print('\nWaiting to receive..')
                try:
                    data, server = sock.recvfrom(4096)
                    # Reset failed trials on successful transmission
                    connection_trials_count = 0
                except:
                    connection_trials_count += 1
                    if connection_trials_count < 5: # arbitrarily set, can be adaptive
                        print("\nConnection time out, retrying")
                        continue
                    else:
                        print("\nMaximum connection trials reached, skipping request\n")
                        # os.remove("r_" + userInput)
                        break
                data = pickle.loads(data)
                seqNo = data.split(delimiter)[1]
                clientHash = hashlib.sha1(pickle.dumps(data.split(delimiter)[3])).hexdigest()
                print("Server hash: " + data.split(delimiter)[0])
                print("Client hash: " + clientHash)
                if data.split(delimiter)[0] == clientHash and seqNoFlag == int(seqNo == True):
                    packetLength = data.split(delimiter)[2]
                    if data.split(delimiter)[3] == "FNF":
                        print("Requested file could not be found on the server")
                        # os.remove("r_" + userInput)
                    else:
                        data_store += data.split(delimiter)[3]
                    print(f"Sequence number: {seqNo}\nLength: {packetLength}")
                    print(f"Server: %s on port {server}")

                    # send ack to sender
                    sent = sock.sendto(pickle.dumps(str(seqNo) + "," + packetLength), server)
                else:
                    print("Checksum mismatch detected, dropping packet")
                    print(f"Server: %s on port {server}")
                    continue
                if int(packetLength) < 500:
                    seqNo = int(not seqNo)
                    break

        finally:
            print("Closing socket")
            sock.close()
            print(data_store)


