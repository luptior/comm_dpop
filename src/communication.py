from utility import *
import socket
import pickle
from network import *


def udp_send(a, title, data, dest_node_id):
    print(str(a.id) + ': udp_send, sending a message ...')

    info = a.agents_info
    pdata = pickle.dumps((title, data))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(pdata, (info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
    sock.close()

    print(str(a.id) + ': Message sent, ' + title + ": " + str(data))


def tcp_send(info, title, data, ori_node_id, dest_node_id):
    sleep(tran_time(sys.getsizeof(data)))

    print(str(ori_node_id) + ': tcp_send, sending a message ...')
    # info = this.agents_info
    pdata = pickle.dumps((title, data))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # TCP
    sock.connect((info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
    sock.send(pdata)

    sock.close()

    print(str(ori_node_id) + ': Message sent to agent ' + str(dest_node_id) + ', ' + title + ": " + str(data))


def listen_func(msgs, sock, agent):
    """
    Continuously listens on the IP and Port specified in 'sock', and stores the
    messages in the dict 'msgs', until an 'exit' message is received. See
    comments in the source code for more information.
    """

    if agent is None:
        agent_id = 'No agent'
    else:
        agent_id = agent.id
    print(str(agent_id) + ': Begin listen_func')

    while True:
        # The 'data' which is received should be the pickled string
        # representation of a tuple.
        # The first element of the tuple should be the data title, a name given
        # to describe the data.
        # This first element will become the key of the 'msgs' dict.
        # The second element should be the actual data to be passed.
        # Loop ends when an exit message is sent.

        # UDP
        # data, addr = sock.recvfrom(65536)
        # udata = pickle.loads(data) # Unpickled data

        # TCP
        connectionSocket, addr = sock.accept()

        total_data = []
        while True:
            data = connectionSocket.recv(4096)
            if not data:
                break
            total_data.append(data)
        data = b''.join(total_data)

        """
        the optimization comes into play
        """
        size = sys.getsizeof(data)

        sleep(tran_time(size))

        udata = pickle.loads(data)  # Unpickled data

        msgs[udata[0]] = udata[1]
        # print(
        #     str(agent_id) + ': Msg received, size is ' + str(len(data)) + " bytes\n" + udata[0] + ": " + str(udata[1]))
        print(str(agent_id) + ': Msg received, size is ' + str(len(data)) + " bytes\n")
        if str(udata[1]) == "exit":
            print(str(agent_id) + ': End listen_func')
            return
