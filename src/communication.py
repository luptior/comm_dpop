"""
communication.py

Contains the functions using different network procotol to send data

Sending functions:
udp_send
udp_send_fec
rudp_send
rudp_send_fec
tcp_send

Receiving function:

listen_func


@auther: gan.xu
"""

import socket
import pickle
import sys
import threading
import time

import network
from network import *

import rs_coding
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

    a.logger.info(f"Message sent to a {str(dest_node_id)}, {title}")


def udp_send_fec(a: agent, title: str, data, dest_node_id):
    a.logger.info(f"udp_send_fec, sending a message with FEC...")

    info = a.agents_info

    pdata = rs_coding.serialize(title, data)
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

    pdata = rs_coding.serialize(title, data)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(pdata, (info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
    except OSError:
        raise OSError(f"Message too long {msg_structure.get_actual_size(pdata)}")

    sock.close()
    if not title == "ACK" and title not in a.waiting_ack:

        if isinstance(data, list) and isinstance(data[0], tuple):  # in split processing format
            a.logger.info(f"Waiting_ack is {a.waiting_ack}, add {title}_{data[0]}")
            if "(" not in title:
                a.waiting_ack.append(f"{title}_{data[0]}")
                a.waiting_ack_time[time.time()] = (f"{title}_{data[0]}", dest_node_id)
                a.outgoing_draft[(f"{title}_{data[0]}", dest_node_id)] = data
            else:
                a.waiting_ack_time[time.time()] = (f"{title}", dest_node_id)
                a.outgoing_draft[(f"{title}", dest_node_id)] = data
        elif isinstance(data, dict) and "value" not in title:  # in pipeline processing format
            if "(" not in title:
                seq = list(data.keys())[0]
                a.logger.info(f"Waiting_ack is {a.waiting_ack}, add {title}_{seq}")
                a.waiting_ack.append(f"{title}_{seq}")
                a.waiting_ack_time[time.time()] = (f"{title}_{seq}", dest_node_id)
                a.outgoing_draft[(f"{title}_{seq}", dest_node_id)] = data
            else:
                a.logger.info(f"Waiting_ack is {a.waiting_ack}, add {title}")
                a.waiting_ack_time[time.time()] = (f"{title}", dest_node_id)
                a.outgoing_draft[(f"{title}", dest_node_id)] = data
        else:
            a.logger.info(f"Waiting_ack is {a.waiting_ack}, add {title}")
            a.waiting_ack.append(title)
            a.waiting_ack_time[time.time()] = (title, dest_node_id)
            a.outgoing_draft[(title, dest_node_id)] = data
        # a.logger.info(str(a.outgoing_draft))

    a.logger.info('Message sent, ' + title + ": " + str(data))


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
    if not title == "ACK" and title not in a.waiting_ack:

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


def listen_func(a: agent, msgs, unprocessed_util, sock):
    """
    Listening on function, and stores the messages in the dict 'msgs'
    Exit when an 'exit' message is received.

    """

    # network parameters
    ber = a.ber
    drop_rate = a.drop
    rtt = a.rtt
    buffer_size = a.buffer_size

    if a is None:
        agent_id = 'No agent'
    else:
        agent_id = a.id

    a.logger.info(f"Begin listen_func")

    properties = prop.load_properties("properties.yaml")
    network_protocol = properties["network_protocol"]

    # Creating and starting the 'listen' thread for auto retransmission
    if network_protocol in ["RUDP", "RUDP_FEC"]:
        resend_thread = threading.Thread(name='Resending-Unpacked-Packet-of-' + str(a.id),
                                         target=resend_noack,
                                         kwargs={'a': a})
        resend_thread.setDaemon(True)
        resend_thread.start()

    while True:
        # The 'data' which is received should be the pickled string representation of a tuple.
        # The first element of the tuple should be the data title, a name given to describe
        # the data. This first element will become the key of the 'msgs' dict. The second
        # element should be the actual data to be passed. Loop ends when an exit message is sent.

        if network_protocol == "UDP":
            data, addr = sock.recvfrom(buffer_size)
            udata = pickle.loads(data)  # Unpickled data

            if a.network_customization:
                a.logger.debug(f"Sleep for {tran_time(a, msg_structure.get_actual_size(data))}")
                sleep(tran_time(a, msg_structure.get_actual_size(data)))

        elif network_protocol == "UDP_FEC":
            data, addr = sock.recvfrom(buffer_size)
            n = size = msg_structure.get_actual_size(data)
            s = 10  # should bee changed to variable
            udata = rs_coding.deserialize(data)

            # network delay time
            if a.network_customization:

                if np.random.random() <= network.rs_rej_prop(size, s, ber):  # where there is error happen
                    a.logger.info("There is an error sleep" + str(2 * tran_time(a, size)))
                    size = msg_structure.get_actual_size(data)
                    sleep(2 * tran_time(a, size))

                sleep(tran_time(a, size))

        elif network_protocol == "TCP":
            connectionSocket, addr = sock.accept()

            # data processing part
            total_data = []
            while True:
                data = connectionSocket.recv(4096)
                if not data:
                    break
                total_data.append(data)
            data = b''.join(total_data)

            size = msg_structure.get_actual_size(data)

            # network delay time
            if a.network_customization:
                # error rate delay part

                network.rs_rej_prop(size, 10, ber)  # run this balance time out
                sleep(2 * tran_time(a, size) / (1 - checksum_rej_prop(size, ber)))
                a.logger.info("There is an error , delay" + str(2 * tran_time(a, size)))

                sleep(tran_time(a, size))
                a.logger.debug(f"Sleep for {tran_time(a, size)}")

            udata = pickle.loads(data)  # Unpickled data

        elif network_protocol == "RUDP":

            data, addr = sock.recvfrom(buffer_size)
            udata = pickle.loads(data)  # Unpickled data

            # regular data message
            #   title: util_msg_{agent_id}
            #   data: ex. [(6,), [219.0, 249.0, 270.0, 239.0]]
            # ACK message:
            #   title: ACK
            #   data: util_msg_{agent_id}_(6,), the title of ack message
            title = udata[0]

            # ACK processing part
            if title == "ACK":
                # if received a ACK, remove it from the listing
                # a.logger.info(f"Received ACK: {udata[1]}")
                a.received_ack.add(udata[1])
                # a.logger.info(f"New ACKs: {udata[1]}")
                # if udata[1] in a.waiting_ack:
                #     a.logger.info(f"Waiting_ack is {a.waiting_ack}, remove {udata[1]}")
                #     a.waiting_ack.remove(udata[1])
                # else ignore, just make sure receiver has got the data
                continue
            else:
                # if not, needs to be ACKed
                if "ptinfo" in title:
                    # title ptinfo doesn't contain source a id
                    a.send("ACK", title, a.root_id)
                    # a.logger.info(f"ACK {title} {a.root_id}")
                elif "pre_util_msg" in title or "value_msg_" in title or "neighbors" in title or "domain" in title:
                    ori_node_id = int(title.split("_")[-1])
                    a.send("ACK", title, ori_node_id)
                else:
                    ori_node_id = int(title.split("_")[-1])
                    a.send("ACK", f"{title}_{udata[1][0]}", ori_node_id)
                    # a.logger.info(f"ACK {title}_{udata[1][0]} {ori_node_id}")

            if a.network_customization:

                # delay and rejection part
                if np.random.random() <= network.rs_rej_prop(size, s, ber):  # where there is error happen
                    a.logger.info("there is an error, dropped and wait")
                    # size = msg_structure.get_actual_size(data)
                    # sleep(2 * tran_time(a, size))
                    continue

                size = msg_structure.get_actual_size(data)
                sleep(tran_time(a, size))

        elif network_protocol == "RUDP_FEC":
            # TODO: to be continued

            data, addr = sock.recvfrom(buffer_size)
            udata = rs_coding.deserialize(data)
            n = size = msg_structure.get_actual_size(data)
            s = 10  # should bee changed to variable
            # regular data message
            #   title: util_msg_{agent_id}
            #   data: ex. [(6,), [219.0, 249.0, 270.0, 239.0]]
            # ACK message:
            #   title: ACK
            #   data: util_msg_{agent_id}_(6,), the title of ack message
            title = udata[0]
            message = udata[1]

            if title == "ACK":
                # if received a ACK, remove it from the listing
                # a.logger.info(f"Received ACK: {udata[1]}")
                a.received_ack.add(udata[1])
                # a.logger.info(f"Received ACKs: {a.received_ack}")
                # if udata[1] in a.waiting_ack:
                #     a.logger.info(f"Waiting_ack is {a.waiting_ack}, remove {udata[1]}")
                #     a.waiting_ack.remove(udata[1])
                # else ignore, just make sure receiver has got the data
                continue
            else:
                # if not, needs to be ACKed
                if "ptinfo" in title:
                    # title ptinfo doesn't contain source a id
                    a.send("ACK", title, a.root_id)
                    # a.logger.info(f"ACK {title} {a.root_id}")
                elif "pre_util_msg" in title or "value_msg_" in title or "neighbors" in title or "domain" in title:
                    ori_node_id = int(title.split("_")[-1])
                    a.send("ACK", title, ori_node_id)
                else:
                    if "(" in title:
                        ori_node_id = int(title.split("_")[-2])
                    else:
                        ori_node_id = int(title.split("_")[-1])
                    if "util_msg_" == title[:9] and isinstance(message, dict):
                        seq = list(message.keys())[0]
                        a.send("ACK", f"{title}_{seq}", ori_node_id)
                        a.logger.info(f"ACK {title}_{seq} {ori_node_id}")
                    else:
                        a.send("ACK", f"{title}_{message[0]}", ori_node_id)

            if a.network_customization:

                if np.random.random() <= network.rs_rej_prop(size, s, ber):  # where there is error happen
                    a.logger.info("There is an error sleep" + str(2 * tran_time(a, size)))
                    # size = msg_structure.get_actual_size(data)
                    # sleep(2 * tran_time(a, size))
                    continue

                sleep(tran_time(a, size))

        # msgs entry example util_msg_1:[[...]]
        msgs[udata[0]] = udata[1]

        # specially desigend for the partial calculation
        if udata[0][:4] == "util":
            unprocessed_util.append(udata)

        # just some record printing
        if len(str(udata[1])) < 100:
            a.logger.info(
                f"Msg received, size is {msg_structure.get_actual_size(data)} bytes"
                f"\n {udata[0]} : {str(udata[1])}")
        else:
            a.logger.info(
                f"Msg received, size is {msg_structure.get_actual_size(data)} bytes"
                f"\n {udata[0]} : {str(udata[1])[:100]} ...")

        # if "value_msg_" in udata[0] and a.is_leaf() :
        #     # for leaf a, end listen func when value msg is received
        #     a.logger.info(f"End listen_func")
        #     return

        # exit only when exit is received
        if str(udata[1]) == "exit":
            a.logger.info(f"End listen_func")
            return

    a.logger.info(f"End listen_func")


def resend_noack(a: agent):
    # resend packet if message ACK not received

    # if set speed is 10 then timeout is 10
    # timeout = 100/a.net_speed

    while True:

        a.waiting_ack = list(set(a.waiting_ack).difference(a.received_ack))
        # update_ack(a)

        if len(a.waiting_ack) > 0:

            oldest_tick = sorted(a.waiting_ack_time)[0]

            data = a.outgoing_draft[a.waiting_ack_time[oldest_tick]]
            size = msg_structure.get_actual_size(data)
            timeout = 10 * tran_time(a, size)

            if time.time() - sorted(a.waiting_ack_time)[0] >= timeout:

                (title, dest_node_id) = a.waiting_ack_time[oldest_tick]
                a.logger.info(
                    f"A resend is needed, {(title, dest_node_id)} packet size is {size}, timeout is {timeout}, not take {time.time() - sorted(a.waiting_ack_time)[0]}")
                # waiting ack + waiting ack timed out

                # resend
                # need to remove the previous one
                if isinstance(data, list) and isinstance(data[0], tuple):  # in split processing format
                    a.logger.info(f"Waiting_ack is {a.waiting_ack}, resend remove {title}_{data[0]}")
                    if f"{title}_{data[0]}" not in a.waiting_ack:
                        a.waiting_ack_time.pop(oldest_tick)
                        continue
                    else:
                        a.waiting_ack.remove(f"{title}_{data[0]}")
                else:
                    a.logger.info(f"Waiting_ack is {a.waiting_ack}, resend remove {title}")
                    if title not in a.waiting_ack:
                        a.waiting_ack_time.pop(oldest_tick)
                        continue
                    else:
                        a.waiting_ack.remove(title)

                a.send(title, a.outgoing_draft[(title, dest_node_id)], dest_node_id)

                # update tick
                a.waiting_ack_time.pop(oldest_tick)
                a.waiting_ack_time[time.time()] = (title, dest_node_id)

            tick_diff = time.time() - sorted(a.waiting_ack_time)[0]
            if tick_diff < timeout:
                sleep(tick_diff)


def update_ack(a: agent):
    # remove received ack
    a.waiting_ack = list(set(a.waiting_ack).difference(a.received_ack))

    t_to_delete = []
    for t, (title, dest_node_id) in a.waiting_ack_time.items():
        if title not in a.waiting_ack:
            t_to_delete.append(t)

    for t in t_to_delete:
        a.waiting_ack_time.pop(t)
