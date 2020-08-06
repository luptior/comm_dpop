import socket
import pickle
import sys
import threading
import time

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
    a.waiting_ack_time[time.time()] = (title, dest_node_id)
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
    if not title == "ACK":
        if isinstance(data, list) and isinstance(data[0], tuple):  # in split processing format
            a.logger.info(f"Waiting_ack is {a.waiting_ack}, add {title}_{data[0]}")
            a.waiting_ack.append(f"{title}_{data[0]}")
            a.waiting_ack_time[time.time()] = (f"{title}_{data[0]}", dest_node_id)
            a.outgoing_draft[(f"{title}_{data[0]}", dest_node_id)] = data
        else:
            a.logger.info(f"Waiting_ack is {a.waiting_ack}, add {title}")
            a.waiting_ack.append(title)
            a.waiting_ack_time[time.time()] = (title, dest_node_id)
            a.outgoing_draft[(title, dest_node_id)] = data
        # a.logger.info(str(a.outgoing_draft))

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

    if network_protocol in ["RUDP", "RUDP_FEC"]:
        # Creating and starting the 'listen' thread
        resend_thread = threading.Thread(name='Resending-Unacked-Packet-of' + str(agent.id),
                                         target=resend_noack,
                                         kwargs={'agent': agent})
        resend_thread.setDaemon(True)
        resend_thread.start()

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

            # regular data message
            #   title: util_msg_{agent_id}
            #   data: ex. [(6,), [219.0, 249.0, 270.0, 239.0]]
            # ACK message:
            #   title: ACK
            #   data: util_msg_{agent_id}_(6,), the title of ack message
            title = udata[0]

            if title == "ACK":
                # if received a ACK, remove it from the listing
                # agent.logger.info(f"Received ACK: {udata[1]}")
                agent.received_ack.add(udata[1])
                # agent.logger.info(f"Received ACKs: {agent.received_ack}")
                # if udata[1] in agent.waiting_ack:
                #     agent.logger.info(f"Waiting_ack is {agent.waiting_ack}, remove {udata[1]}")
                #     agent.waiting_ack.remove(udata[1])
                # else ignore, just make sure receiver has got the data
                continue
            else:
                # if not, needs to be ACKed
                if "ptinfo" in title:
                    # title ptinfo doesn't contain source agent id
                    agent.send("ACK", title, agent.root_id)
                    # agent.logger.info(f"ACK {title} {agent.root_id}")
                elif "pre_util_msg" in title or "value_msg_" in title or "neighbors" in title or "domain" in title:
                    ori_node_id = int(title.split("_")[-1])
                    agent.send("ACK", title, ori_node_id)
                else:
                    ori_node_id = int(title.split("_")[-1])
                    agent.send("ACK", f"{title}_{udata[1][0]}", ori_node_id)
                    # agent.logger.info(f"ACK {title}_{udata[1][0]} {ori_node_id}")

            if agent.network_customization:
                size = msg_structure.get_actual_size(data)
                sleep(tran_time(agent, size))

        elif network_protocol == "RUDP_FEC":
            # TODO: to be continued

            data, addr = sock.recvfrom(65536)
            udata = pickle.loads(data)  # Unpickled data

            if agent.network_customization:
                size = msg_structure.get_actual_size(data)
                sleep(tran_time(agent, size))

        # msgs entry example util_msg_1:[[...]]
        msgs[udata[0]] = udata[1]

        # specially desigend for the partial calculation
        if udata[0][:4] == "util":
            unprocessed_util.append(udata)

        # just some record printing
        if len(str(udata[1])) < 100:
            agent.logger.info(
                f"Msg received, size is {msg_structure.get_actual_size(data)} bytes\n {udata[0]} : {str(udata[1])}")
        else:
            agent.logger.info(
                f"Msg received, size is {msg_structure.get_actual_size(data)} bytes\n {udata[0]} : {str(udata[1])[:100]} ...")

        if "value_msg_" in udata[0] and agent.is_leaf():
            # for leaf agent, end listen func when value msg is received
            agent.logger.info(f"End listen_func")
            return

        # exit only when exit is received
        if str(udata[1]) == "exit":
            agent.logger.info(f"End listen_func")
            return

    agent.logger.info(f"End listen_func")


def resend_noack(agent):
    # resend packet if message ACK not received

    # if set speed is 10 then timeout is 10
    # timeout = 100/agent.net_speed

    while True:

        agent.waiting_ack = list(set(agent.waiting_ack).difference(agent.received_ack))

        if len(agent.waiting_ack) > 0:

            oldest_tick = sorted(agent.waiting_ack_time)[0]

            (title, dest_node_id) = agent.waiting_ack_time[oldest_tick]

            if title in agent.received_ack:
                agent.waiting_ack_time.pop(oldest_tick)
                continue

            data = agent.outgoing_draft[agent.waiting_ack_time[oldest_tick]]
            size = msg_structure.get_actual_size(data)
            timeout = 10 * tran_time(agent, size)

            if time.time() - sorted(agent.waiting_ack_time)[0] >= timeout:

                (title, dest_node_id) = agent.waiting_ack_time[oldest_tick]
                agent.logger.info(
                    f"A resend is needed, {(title, dest_node_id)} packet size is {size}, timeout is {timeout}, not take {time.time() - sorted(agent.waiting_ack_time)[0]}")
                # waiting ack + waiting ack timed out

                # resend
                # need to remove the previous one
                if isinstance(data, list) and isinstance(data[0], tuple):  # in split processing format
                    agent.logger.info(f"Waiting_ack is {agent.waiting_ack}, resend remove {title}_{data[0]}")
                    if f"{title}_{data[0]}" not in agent.waiting_ack:
                        agent.waiting_ack_time.pop(oldest_tick)
                        continue
                    else:
                        agent.waiting_ack.remove(f"{title}_{data[0]}")
                else:
                    agent.logger.info(f"Waiting_ack is {agent.waiting_ack}, resend remove {title}")
                    if title not in agent.waiting_ack:
                        agent.waiting_ack_time.pop(oldest_tick)
                        continue
                    else:
                        agent.waiting_ack.remove(title)

                agent.send(title, agent.outgoing_draft[(title, dest_node_id)], dest_node_id)

                # update tick
                agent.waiting_ack_time.pop(oldest_tick)
                agent.waiting_ack_time[time.time()] = (title, dest_node_id)

            tick_diff = time.time() - sorted(agent.waiting_ack_time)[0]
            if tick_diff < timeout:
                sleep(tick_diff)
