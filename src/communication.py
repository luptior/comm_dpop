import socket
import pickle
import sys

import network
from network import *

import RSCoding
import properties as prop
import agent
import msg_structure


def udp_send(a: agent, title, data, dest_node_id):
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


def tcp_send(a: agent, title: str, data, ori_node_id, dest_node_id):
    info = a.agents_info
    a.logger.info(f"tcp_send, sending a message ...")

    # TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))

    pdata = pickle.dumps((title, data))
    sock.send(pdata)
    sock.close()

    a.logger.info(f"Message sent to agent {str(dest_node_id)}, {title}")


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


def rudp_send_fec(a: agent, title: str, data, dest_node_id):
    a.logger.info(f"rudp_send_fec, sending a message with FEC...")
    info = a.agents_info

    a.waiting_ack.append(title)
    return

def rudp_send(a: agent, title: str, data, dest_node_id):
    a.logger.info(f"rudp_send, sending a message with just rudp...")
    info = a.agents_info

    pdata = pickle.dumps((title, data))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(pdata, (info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
    except OSError:
        a.logger.error(f"Message too long {msg_structure.get_actual_size(pdata)}")
        raise

    sock.close()
    a.waiting_ack.append(title)
    a.logger.info('Message sent, ' + title + ": " + str(data))



def listen_func(msgs, unprocessed_util, sock, agent):
    """
    Listening on function, and stores the messages in the dict 'msgs'
    Exit when an 'exit' message is received.

    Used in pseudotree_creation
    """

    ber = 10 ** -4

    if agent is None:
        agent_id = 'No agent'
    else:
        agent_id = agent.id

    agent.logger.info(f"Begin listen_func")

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

            if agent.network_customization:
                size = msg_structure.get_actual_size(data)
                sleep(tran_time(agent, size))
        elif network_protocol == "UDP_FEC":
            data, addr = sock.recvfrom(65535)
            n = size = msg_structure.get_actual_size(data)
            s = 10  # should bee changed to variable
            udata = RSCoding.deserialize(data)

            if np.random.random() <= network.rs_rej_prop(size, s, ber):  # where there is error happen
                print("there is an error sleep" + str(2 * tran_time(agent, size)))
                size = msg_structure.get_actual_size(data)
                sleep(2 * tran_time(agent, size))

            if agent.network_customization:
                size = msg_structure.get_actual_size(data)
                sleep(tran_time(agent, size))

        elif network_protocol == "TCP":
            connectionSocket, addr = sock.accept()

            total_data = []
            while True:
                data = connectionSocket.recv(4096)
                if not data:
                    break
                total_data.append(data)
            data = b''.join(total_data)

            size = msg_structure.get_actual_size(data)

            if agent.network_customization:
                sleep(tran_time(agent, size))

            if np.random.random() <= 1 - np.power(1 - ber,
                                                  msg_structure.get_actual_size(data)):  # where there is error happen
                sleep(2 * tran_time(agent, size))
                print("there is an error , delay" + str(2 * tran_time(agent, size)))

            udata = pickle.loads(data)  # Unpickled data

        elif network_protocol == "RUDP":
            data, addr = sock.recvfrom(65536)
            udata = pickle.loads(data)  # Unpickled data

            title = udata[0] # util_msg_{agent_id}_seq

            # ACK messge:
            #   title: ACK
            #   data: util_msg_{agent_id}_seq, the title of ack message

            if title == "ACK":
                agent.waiting_ack.remove(udata[1])
                continue
            else: # if not, needs to be acked
                if "/" in title: # contains seq
                    agent.send("ACK", title, title.split("_")[-2])
                else:
                    agent.send("ACK", title, title.split("_")[-1])


        elif network_protocol == "RUDP_FEC":
            #TODO: to be continued

            data, addr = sock.recvfrom(65536)
            udata = pickle.loads(data)  # Unpickled data



        # msgs entry example util_msg_1:[[...]]
        msgs[udata[0]] = udata[1]

        # specially desigend for the partial calculation
        if udata[0][:4] == "util":
            unprocessed_util.append(udata)

        # just some record printing
        if len(str(udata[1])) < 100:
            agent.logger.info(f"Msg received, size is {str(sys.getsizeof(data))} bytes\n {udata[0]} : {str(udata[1])}")
        else:
            agent.logger.info(
                f"Msg received, size is {str(sys.getsizeof(data))} bytes\n {udata[0]} : {str(udata[1])[:100]} ...")

        # exit only when exit is received
        if str(udata[1]) == "exit":
            agent.logger.info(f"End listen_func")
            return
