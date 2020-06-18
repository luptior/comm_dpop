import socket
import pickle
import sys
from datetime import datetime as dt

from network import *

import RSCoding
import properties as prop
import agent
import msg_structure


def udp_send(a: agent, title, data, dest_node_id):
    # print(str(a.id) + ': udp_send, sending a message ...')
    a.logger.info('Udp_send, sending a message ...')

    info = a.agents_info
    pdata = pickle.dumps((title, data))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(pdata, (info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
    except OSError:
        a.logger.error(f"Message too long {msg_structure.get_actual_size(pdata)}")
        raise
    sock.close()

    a.logger.info('Message sent, ' + title + ": " + str(data))
    # print(str(a.id) + ': Message sent, ' + title + ": " + str(data))


def tcp_send(a: agent, title: str, data, ori_node_id, dest_node_id):
    info = a.agents_info
    # print(dt.now(), str(ori_node_id) + ': tcp_send, sending a message ...')
    a.logger.info(f"{dt.now()} : tcp_send, sending a message ...")

    # TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))

    pdata = pickle.dumps((title, data))
    sock.send(pdata)
    sock.close()

    # print(str(ori_node_id) + ': Message sent to agent ' + str(dest_node_id) + ', ' + title + ": " + str(data))
    # print(dt.now(), str(ori_node_id) + ': Message sent to agent ' + str(dest_node_id) + ', ' + title)
    a.logger.info(f"{dt.now()}: Message sent to agent {str(dest_node_id)}, {title}")


def udp_send_fec(a: agent, title: str, data, dest_node_id):
    a.logger.info(f"udp_send_fec, sending a message with FEC...")

    info = a.agents_info

    pdata = RSCoding.serialize(title, data)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(pdata, (info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
    except OSError:
        a.logger.error(f"Message too long {msg_structure.get_actual_size(pdata)}")
        raise
    sock.close()

    a.logger.info(f" Message sent, {title} : {str(data)[:100]} ...")


def listen_func(msgs, unprocessed_util, sock, agent):
    """
    Listening on function, and stores the messages in the dict 'msgs'
    Exit when an 'exit' message is received.

    Used in pseudotree_creation
    """

    if agent is None:
        agent_id = 'No agent'
    else:
        agent_id = agent.id

    agent.logger.info(f"{dt.now()}  Begin listen_func")

    properties = prop.load_properties("properties.yaml")
    network_protocol = properties["network_protocol"]

    while True:
        # The 'data' which is received should be the pickled string representation of a tuple.
        # The first element of the tuple should be the data title, a name given to describe
        # the data. This first element will become the key of the 'msgs' dict. The second
        # element should be the actual data to be passed. Loop ends when an exit message is sent.

        if network_protocol == "UDP":
            data, addr = sock.recvfrom(65536)
            udata = pickle.loads(data)  # Unpickled data
        elif network_protocol == "UDP_FEC":
            data, addr = sock.recvfrom(65535)
            udata = RSCoding.deserialize(data)
        elif network_protocol == "TCP":
            connectionSocket, addr = sock.accept()

            total_data = []
            while True:
                data = connectionSocket.recv(4096)
                if not data:
                    break
                total_data.append(data)
            data = b''.join(total_data)

            if agent.network_customization:
                size = sys.getsizeof(data)
                sleep(tran_time(agent, size))

            if True: # where there is error happen
                logger
                if np.random.random() <= 1/1100:
                    size = sys.getsizeof(data)
                    sleep(tran_time(agent, size))

            udata = pickle.loads(data)  # Unpickled data

        # msgs entry example util_msg_1:[[...]]
        msgs[udata[0]] = udata[1]

        # specially desigend for the partial calculation
        if udata[0][:4] == "util":
            unprocessed_util.append(udata)

        # just some record printing
        if len(str(udata[1])) < 100:
            agent.logger.info(f"{dt.now()} : Msg received, size is {str(sys.getsizeof(data)) } bytes\n {udata[0]} : {str(udata[1])}")
        else:
            agent.logger.info(f"{dt.now()} : Msg received, size is {str(sys.getsizeof(data)) } bytes\n {udata[0]} : {str(udata[1])[:100]} ...")

        # exit only when exit is received
        if str(udata[1]) == "exit":
            agent.logger.info(f"{dt.now()} : End listen_func")
            return
