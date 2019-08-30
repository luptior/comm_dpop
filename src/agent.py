"Defines the class Agent which represents a node/agent in the DPOP algorithm."

import utility
import pickle
import socket
import sys
from time import sleep
import logging

import pseudotree_creation
import util_msg_prop
import value_msg_prop
from network_optimize import *

logger = logging.getLogger("dpop.agent")


class Agent:
    def __init__(self, i, domain, relations, agents_file):
        # Use utils.get_agents_info to initialize all the agents.
        # All the information from 'agents.txt' will be retrieved and stored in this dict 'agents_info'.
        # Also, the domains of some agents will be added to this dict later on.
        # You can access a value as:
        # agent.agents_info[<agent_id>]['field_required']
        # Some miscellaneous information will be stored with id=42.
        self.agents_info = utility.get_agents_info(agents_file)
        info = self.agents_info

        self.value = -1  # The value that will be selected for this agent
        self.max_util = float("-inf")  # Will be initialized only for the root, in the end
        self.i = self.id = i
        self.domain = domain  # A list of values
        self.relations = relations  # A dict of functions, for each edge in the
        # graph
        self.graph_nodes = self.get_graph_nodes()  # A list of all the nodes in
        # the graph, except itself
        self.neighbors = self.get_neighbors()  # A list of all the neighbors
        # sorted by ids
        self.p = None  # The parent's id
        self.pp = None  # A list of the pseudo-parents' ids
        self.c = None  # A list of the childrens' ids
        self.pc = None  # A list of the pseudo-childrens' ids
        self.table = None  # The table that will be stored
        self.table_ant = None  # The ANT of the table that will be stored
        self.IP = info[self.id]['IP']
        self.PORT = eval(info[self.id]['PORT'])  # Listening Port
        self.is_root = False
        if 'is_root' in info[self.i]:
            self.is_root = eval(info[self.i]['is_root'])
        self.root_id = eval(info[42]['root_id'])
        self.msgs = {}  # The dict where all the received messages are stored

    def get_graph_nodes(self):
        info = self.agents_info
        graph_nodes = []
        for key in info:
            if key != 42 and key != self.id:
                graph_nodes.append(key)
        return graph_nodes

    def get_neighbors(self):
        L = []
        for first, second in self.relations.keys():
            if first == self.i:
                L.append(second)
            else:
                L.append(first)
        return sorted(L)

    def calculate_util(self, tup, xi):
        """
        Calculates the util; given a tuple 'tup' which has the assignments of
        values of parent and pseudo-parent nodes, in order; given a value 'xi'
        of this agent.
        """

        # Assumed that utilities are combined by adding to each other
        try:
            util = self.relations[self.id, self.p][xi, tup[0]]
        except KeyError:
            util = 0

        for index, x in enumerate(tup[1:]):
            try:
                util = util + self.relations[self.id, self.pp[index]][xi, x]
            except KeyError:
                continue
        return util

    def is_leaf(self):
        "Return True if this node is a leaf node and False otherwise."

        assert self.c != None, 'self.c not yet initialized.'
        if self.c == []:
            return True
        else:
            return False

    def udp_send(self, title, data, dest_node_id):
        # print(str(self.id) + ': udp_send, sending a message ...')
        logger.info(str(self.id) + ': udp_send, sending a message ...')

        info = self.agents_info
        pdata = pickle.dumps((title, data))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(pdata, (info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
        sock.close()

        logger.info(str(self.id) + ': Message sent, ' + title + ": " + str(data))
        # print(str(self.id) + ': Message sent, ' + title + ": " + str(data))

    def tcp_send(self, title, data, dest_node_id):

        sleep(tran_time(sys.getsizeof(data)))

        logger.info(str(self.id) + ': tcp_send, sending a message ...')
        # print(str(self.id) + ': tcp_send, sending a message ...')
        info = self.agents_info
        pdata = pickle.dumps((title, data))

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # TCP
        sock.connect((info[dest_node_id]['IP'], int(info[dest_node_id]['PORT'])))
        sock.send(pdata)

        sock.close()
        logger.info(str(self.id) + ': Message sent to agent ' + str(dest_node_id) + ', ' + title + ": " + str(data))
        # print(str(self.id) + ': Message sent to agent ' + str(dest_node_id) + ', ' + title + ": " + str(data))

    def start(self):

        logger.info(str(self.id) + ': Started')
        # print(str(self.id) + ': Started')
        pseudotree_creation.pseudotree_creation(self)
        util_msg_prop.util_msg_prop(self)
        if not self.is_root:
            value_msg_prop.value_msg_prop(self)

        # print(str(self.id) + ': Finished')
        logger.info(str(self.id) + ': Finished')
