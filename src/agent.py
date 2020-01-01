"""
Defines the class Agent which represents a node/agent in the DPOP algorithm.
Agent: basic agent class
ListAgent: use instead of ndarray as message
SplitAgent: split message based on optimization
PipelineAgent: do optimization at root and pipeline at non-leaf nodes

"""

from datetime import datetime as dt

import pseudotree_creation
import util_msg_prop
import value_msg_prop
import communication
import utility
import logging

logger = logging.getLogger("AGENT")
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler("log.txt")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Agent:

    def __init__(self, i, domain, relations, agents_file, comp_speed, net_speed):

        """
        Constructor method
        :param i: agent id
        :param domain: agent domain, a list of values
        :param relations: A dict of functions, for each edge in the graph
        :param agents_file:
        """

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
        self.relations = relations  # A dict of functions, for each edge in the graph
        self.graph_nodes = self.get_graph_nodes()  # A list of all the nodes in the graph, except itself
        self.neighbors = self.get_neighbors()  # A list of all the neighbors sorted by ids

        self.p = None  # The parent's id
        self.pp = None  # A list of the pseudo-parents' ids
        self.c = None  # A list of the children's ids
        self.pc = None  # A list of the pseudo-children's ids

        self.table = None  # The table that will be stored
        self.table_ant = None  # The ANT of the table that will be stored, assignment-nodeid-tuples 'ants'.
        self.is_root = False if 'is_root' not in info[self.i] else eval(info[self.i]['is_root'])
        self.root_id = eval(info[42]['root_id'])

        self.msgs = {}  # The dict where all the received messages are stored
        self.unprocessed_util = []  # The dict where all the received util_messages are stored,
        # added for split processing

        self.split_processing = False

        self.IP = info[self.id]['IP']
        self.PORT = eval(info[self.id]['PORT'])  # Listening Port

        if comp_speed:
            self.slow_processing = True
            self.comp_speed = comp_speed
        else:
            self.slow_processing = False
            self.comp_speed=False

        if net_speed:
            self.network_customization = True
            self.net_speed = net_speed
        else:
            self.network_customization = False
            self.net_speed =False

        self.logger = logging.getLogger(f"Agent {self.i}")
        self.logger.info(f"{self.i} is initialized")

    def get_graph_nodes(self):
        info = self.agents_info
        graph_nodes = []
        for key in info:
            if key != 42 and key != self.id:
                graph_nodes.append(key)
        return graph_nodes

    def get_neighbors(self):
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
        assert self.c is not None, 'self.c not yet initialized.'
        self.logger.info(f"{self.i} is leaf node")

        if not self.c:
            return True
        else:
            return False

    def start(self):
        """
        begin the processing
        """

        print(dt.now(), str(self.id) + ': Started')

        pseudotree_creation.pseudotree_creation(self)
        print(f"Split processing is {self.split_processing}\n" +
              f"computation speed is {self.comp_speed} \n" +
              f"network customization is {self.network_customization} \n" +
              f"network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)
        print(dt.now(), str(self.id) + ': Finished')

    def send(self, title, data, dest_node_id):
        """
        a wrap of underlying TCP/UDP in communication
        :param title: msg title
        :param data: the actual data part
        :param dest_node_id: assigned agent id
        """
        communication.tcp_send(self.agents_info, title, data, self.id, dest_node_id)


class PipelineAgent(Agent):
    def __init__(self, i, domain, relations, agents_file, comp_speed, net_speed):
        Agent.__init__(self, i, domain, relations, agents_file, comp_speed, net_speed)
        self.split_processing = True

    def start(self):
        """
        begin the processing
        """

        print(dt.now(), str(self.id) + ': Started')

        pseudotree_creation.pseudotree_creation(self)
        print(f"Split processing is {self.split_processing}\n" +
              f"computation speed is {self.comp_speed} \n" +
              f"network customization is {self.network_customization} \n" +
              f"network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop_split_pipeline(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)
        print(dt.now(), str(self.id) + ': Finished')


class SplitAgent(Agent):
    def __init__(self, i, domain, relations, agents_file, comp_speed, net_speed):
        Agent.__init__(self, i, domain, relations, agents_file, comp_speed, net_speed)
        self.split_processing = True

    def start(self):
        """
        begin the processing
        """

        print(dt.now(), str(self.id) + ': Started')

        pseudotree_creation.pseudotree_creation(self)
        print(f"Split processing is {self.split_processing}\n" +
              f"computation speed is {self.comp_speed} \n" +
              f"network customization is {self.network_customization} \n" +
              f"network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop_split(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)
        print(dt.now(), str(self.id) + ': Finished')


class ListAgent(Agent):
    def __init__(self, i, domain, relations, agents_file, comp_speed, net_speed):
        Agent.__init__(self, i, domain, relations, agents_file, comp_speed, net_speed)

    def start(self):
        """
        begin the processing
        """

        print(dt.now(), str(self.id) + ': Started')

        pseudotree_creation.pseudotree_creation(self)
        print(f"Split processing is {self.split_processing}\n" +
              f"computation speed is {self.comp_speed} \n" +
              f"network customization is {self.network_customization} \n" +
              f"network speed is {self.net_speed} ")

        util_msg_prop.util_msg_prop_list(self)

        if not self.is_root:
            value_msg_prop.value_msg_prop(self)
        print(dt.now(), str(self.id) + ': Finished')
