"""
Defines the class Agent which represents a node/agent in the DPOP algorithm.
Agent: basic agent class
ListAgent: use instead of nd-array as message
SplitAgent: split message based on optimization
PipelineAgent: do optimization at root and pipeline at non-leaf nodes

"""
import time

import pseudotree_creation
import util_msg_prop
import value_msg_prop
import communication
import utility
import logging

from reedsolo import RSCodec
import rs_coding
import properties as prop


class Agent:

    def __init__(self, i, domain, relations: dict, network_properties: dict):

        """
        Constructor method
        :param i: agent id
        :param domain: agent domain, a list of values
        :param relations: A dict of functions, for each edge in the graph
        :param network_properties:
        """

        # Use utils.get_agents_info to initialize all the agents.
        # All the information from 'agents.txt' will be retrieved and stored in this dict 'agents_info'.
        # Also, the domains of some agents will be added to this dict later on.
        # You can access a value as:
        # agent.agents_info[<agent_id>]['field_required']
        # Some miscellaneous information will be stored with id='root'.
        self.agents_info = network_properties
        info = self.agents_info

        self.value = -1  # The value that will be selected for this agent
        self.max_util = float("-inf")  # Will be initialized only for the root, in the end
        self.i = self.id = i
        self.domain = domain  # A list of values
        self.relations = relations  # A dict of functions, for each edge in the graph
        self.graph_nodes = self.get_graph_nodes()  # A list of all the nodes in the graph, except itself
        self.neighbors = self.get_neighbors()  # A list of all the neighbors sorted by ids

        self.p = None  # The parent's id
        self.pp = None  # A list of the pseudo-parents' ids
        self.c = None  # A list of the children's ids
        self.pc = None  # A list of the pseudo-children's ids

        self.table = None  # The table that will be stored
        self.table_ant = None  # The ANT of the table that will be stored, assignment-nodeid-tuples 'ants'.
        self.is_root = False if 'is_root' not in info[self.i] else info[self.i]['is_root']
        self.root_id = int(info['root']['root_id'])

        self.msgs = {}  # The dict where all the received messages are stored

        # properties, the part reads from properties
        properties = prop.load_properties("properties.yaml")
        self.network_protocol = properties["network_protocol"] # TCP/UDP/UDP_FEC
        self.slow_processing = properties["slow_processing"] # whether slowing down is applied
        self.comp_speed = int(properties["comp_speed"]) # c
        self.network_customization = properties["network_customization"]
        self.net_speed = int(properties["net_speed"])
        self.ber = float(properties["ber"])

        self.unprocessed_util = []  # The dict where all the received util_messages are stored,
        # added for split processing

        self.waiting_ack = [] # the list that each call of send using rudp will send to
        self.received_ack = set([])  # the list that each call of send using rudp will send to
        self.waiting_ack_time = {}
        self.outgoing_draft = {}  # the dict {waiting_ack: actual data}, for the need ot resending

        self.split_processing = False

        self.IP = info[self.id]['IP']
        self.PORT = int(info[self.id]['PORT'])  # Listening Port

        # logger initialize
        self.logger = logging.getLogger(f"Agent.{self.i}")
        self.logger.setLevel(level=logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(properties["log_file"])
        fh.setLevel(logging.INFO)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        self.logger.info(f" is initialized IP: {self.IP} Port: {self.PORT}")

    def get_graph_nodes(self) -> list:
        graph_nodes = []
        for key in self.agents_info:
            if key != 'root' and key != self.id:
                graph_nodes.append(key)
        return graph_nodes

    def get_neighbors(self) -> list:
        neighbors = []
        for first, second in self.relations.keys():
            if first == self.i:
                neighbors.append(second)
            else:
                neighbors.append(first)
        return sorted(neighbors)

    def calculate_util(self, tup, xi):
        """
        Calculates the util; given a tuple 'tup' which has the assignments of
        values of parent and pseudo-parent nodes, in order; given a value 'xi'
        of this agent.

        Assumed that utilities are combined by adding to each other
        """
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

    def is_leaf(self) -> bool:
        """
        determine if it is a lead node
        """
        assert self.c is not None, self.logger.error(f'{self.c} not yet initialized.')

        if not self.c:
            return True
        else:
            return False

    def start(self):
        """
        begin the processing
        """

        self.logger.info(f"Started")

        pseudotree_creation.pseudotree_creation(self)
        self.logger.info(f"Split processing is {self.split_processing}, computation speed is {self.comp_speed} \n "
                         f"network customization is {self.network_customization}, network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)

        while len(self.waiting_ack) > 0:
            time.sleep(0.1)
        self.logger.info(f"Finished")

    def send(self, title, data, dest_node_id):
        """
        a wrap of underlying TCP/UDP in communication
        :param title: msg title
        :param data: the actual data part
        :param dest_node_id: assigned agent id
        """
        if self.network_protocol == "UDP":
            communication.udp_send(self, title, data, dest_node_id)
        elif self.network_protocol == "UDP_FEC":
            communication.udp_send_fec(self, title, data, dest_node_id)
        elif self.network_protocol == "TCP":
            communication.tcp_send(self, title, data, self.id, dest_node_id)
        elif self.network_protocol == "RUDP":
            communication.rudp_send(self, title, data, dest_node_id)
        elif self.network_protocol == "RUDP_FEC":
            communication.rudp_send_fec(self, title, data, dest_node_id)


class PipelineAgent(Agent):
    def __init__(self, i, domain, relations, network_properties):
        Agent.__init__(self, i, domain, relations, network_properties)
        self.split_processing = True

    def start(self):
        """
        begin the processing
        """

        self.logger.info(f" Started")

        pseudotree_creation.pseudotree_creation(self)
        self.logger.info(f"Split processing is {self.split_processing}, computation speed is {self.comp_speed} \n "
                         f"network customization is {self.network_customization}, network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop_split_pipeline(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)

        while len(self.waiting_ack) > 0:
            time.sleep(0.1)
            self.logger.info(self.waiting_ack)
        self.logger.info(f"Finished All Acks:{self.received_ack}")


class SplitAgent(Agent):
    def __init__(self, i, domain, relations, network_properties):
        Agent.__init__(self, i, domain, relations, network_properties)
        self.split_processing = True

    def start(self):
        """
        begin the processing
        """

        self.logger.info(f"Started")

        pseudotree_creation.pseudotree_creation(self)
        self.logger.info(f"Split processing is {self.split_processing}, computation speed is {self.comp_speed} \n "
                         f"network customization is {self.network_customization}, network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop_split(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)

        counter = 100 # only repeat 100 times
        while len(self.waiting_ack) > 0 and counter > 0:
            time.sleep(0.1)
            self.logger.info(self.waiting_ack)
            counter -= 0
        self.logger.info(f"Finished All Acks:{self.received_ack}")


class ListAgent(Agent):
    def __init__(self, i, domain, relations, network_properties):
        Agent.__init__(self, i, domain, relations, network_properties)

    def start(self):
        """
        begin the processing
        """

        self.logger.info(f"Started")

        pseudotree_creation.pseudotree_creation(self)
        self.logger.info(f"Split processing is {self.split_processing}, computation speed is {self.comp_speed} \n "
                         f"network customization is {self.network_customization}, network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop_list(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)

        while len(self.waiting_ack) > 0:
            time.sleep(0.1)
        self.logger.info(f"Finished")
