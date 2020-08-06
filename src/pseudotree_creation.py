"""
This module handles the initial part of the algorithm, which is the pseudo-tree
creation.
"""

import threading
import socket
import time

import utility
import pseudotree
import properties as prop
import communication

Relatives = utility.Relatives


def bfs(tree, tree_node, procedure, *extra_procedure_args):
    """"
    Run a the 'procedure' recursively, in a breadth-first-search way, starting
    from the 'tree_node' in the 'tree'.
    """

    # print extra_procedure_args
    # agent, graph, parents, pstree, depths = extra_procedure_args
    procedure(tree_node, *extra_procedure_args)
    for child in tree[tree_node]:
        bfs(tree, child, procedure, *extra_procedure_args)


def tell_relative(node_id, agent, graph, parents, pstree, depths):
    """
    Send a message titled 'ptinfo', which tells the agent with 'node_id'
    its (p, pp, c, pc). Only the root is supposed to call this procedure.
    Hence, if the 'node_id' is of the root itself, it simply sets the
    appropriate fields.
    """

    # Only the root calls this function
    assert agent.is_root == True

    p = parents[node_id]
    c = pstree[node_id]
    pp = []
    pc = []
    pseudo_relatives = set(graph[node_id]) - set([p]) - set(c)
    pseudo_relatives = list(pseudo_relatives)
    for relative in pseudo_relatives:
        if depths[node_id] < depths[relative]:
            pc.append(relative)
        else:
            pp.append(relative)

    # Set appropriate the fields if node_id is same as root_id, or send the
    # 'ptinfo' message otherwise.
    if node_id == agent.root_id:
        agent.p, agent.pp, agent.c, agent.pc = p, pp, c, pc
    else:
        # agent.udp_send('ptinfo', Relatives(p, pp, c, pc), node_id)
        agent.send(f'ptinfo_{node_id}', Relatives(p, pp, c, pc), node_id)
        # agent.tcp_send('ptinfo', Relatives(p, pp, c, pc), node_id)


def pseudotree_creation(agent):
    agent.logger.info(f"Begin pseudotree_creation")
    # The dict where all the messages are stored
    msgs = agent.msgs
    unprocessed_util = agent.unprocessed_util

    properties = prop.load_properties("properties.yaml")
    network_protocol = properties["network_protocol"]

    info = agent.agents_info

    if network_protocol in ['UDP', "UDP_FEC", "RUDP", "RUDP_FEC"]:
        # UDP
        listening_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listening_socket.bind((info[agent.id]['IP'], int(info[agent.id]['PORT'])))
    elif network_protocol in ["TCP"]:
        listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listening_socket.bind((info[agent.id]['IP'], int(info[agent.id]['PORT'])))
        listening_socket.listen(20)

    # Creating and starting the 'listen' thread
    listen = threading.Thread(name='Listening-Thread-of-Agent-' + str(agent.id),
                              target=communication.listen_func,
                              args=(msgs, unprocessed_util, listening_socket),
                              kwargs={'agent': agent})
    listen.setDaemon(True)
    listen.start()

    # Wait before all agents have started listening
    time.sleep(2)

    if agent.is_root:
        # Wait till the each agent sends its neighbors' list.
        while True:
            all_neighbor_msgs_arrived = True
            for node in agent.graph_nodes:
                if ('neighbors_' + str(node)) not in msgs:
                    all_neighbor_msgs_arrived = False
                    break
            if all_neighbor_msgs_arrived:
                break

        # Create the graph and use it to generate the pseudo-tree structure.
        graph = {agent.id: agent.neighbors}
        for key, value in msgs.items():
            if key[0:10] == 'neighbors_':
                graph[int(key[10:])] = list(value)
        pstree = {}
        pstree = pseudotree.dfsTree(graph, agent.id)

        # Set own fields and tell (p, pp, c, pc) to all nodes
        parents = pseudotree.get_parents(pstree)
        depths = pseudotree.assign_depths(pstree)
        bfs(
            pstree,
            pstree['Nothing'][0],
            tell_relative,
            agent, graph, parents, pstree, depths
        )

        # Send this node's (root's) domain to all children and pseudochildren
        # For example, if root's id is 1, the message is, in title:value form:
        # domain_1: <the set which is the domain of 1>
        for child in agent.c + agent.pc:
            # agent.udp_send('domain_'+str(agent.id), agent.domain, child)
            agent.send('domain_' + str(agent.id), agent.domain, child)

    # Procedure for agent other than root
    else:
        agent.send('neighbors_' + str(agent.id), agent.neighbors, agent.root_id)
        # agent.udp_send('neighbors_'+str(agent.id), agent.neighbors, agent.root_id)
        # agent.tcp_send('neighbors_'+str(agent.id), agent.neighbors, agent.root_id)

        # Wait till the message (p, pp, c, pc) [has title: 'ptinfo'] arrives
        # from the root.
        while 'ptinfo_' + str(agent.id) not in agent.msgs:
            pass

        # Initialize all the respective fields
        agent.p, agent.pp, agent.c, agent.pc = agent.msgs['ptinfo_' + str(agent.id)]

        # Send this node's domain to all children and pseudochildren.
        # For example, if this node's id is 7, the message is, in title:value
        # form would be:
        # domain_7: <the set which is the domain of 7>
        for child in agent.c + agent.pc:
            # agent.udp_send('domain_'+str(agent.id), agent.domain, child)
            agent.send('domain_' + str(agent.id), agent.domain, child)
            # agent.tcp_send('domain_' + str(agent.id), agent.domain, child)

        # Wait for the 'domain' message from all parents and pseudoparents.
        # These messages sent will have the form:
        # 'domain_3': set(1, 23, 12, 41, 2, 122)
        while True:
            all_parents_msgs_arrived = True
            for parent in [agent.p] + agent.pp:
                if ('domain_' + str(parent)) not in msgs:
                    # agent.logger.info(f"{('domain_' + str(parent))} not in {msgs.keys()}")
                    all_parents_msgs_arrived = False
                    break
            if all_parents_msgs_arrived:
                agent.logger.info(f": all_parents_msgs_arrived")
                break

        # Store all these domains that have arrived as messages.
        info = agent.agents_info
        for parent in [agent.p] + agent.pp:
            info[parent]['domain'] = msgs['domain_' + str(parent)]

    agent.logger.info(f"End pseudotree_creation")
