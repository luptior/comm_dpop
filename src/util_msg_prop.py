"""
This module implements the functions required by the util_msg_propogation
part of the DPOP algorithm
"""

import sys
import numpy as np
import itertools
import sys
import logging
from time import sleep

import agent
import utility
import optimization
import msg_structure


def swap(indices: tuple, location: int, dest: int = -1) -> tuple:
    new_indices = list(indices)
    new_indices[dest] = indices[location]
    new_indices[location] = indices[dest]
    return tuple(new_indices)


def slow_process(agent, msg):
    """
    sleep by a certain amount of time based on the size of msg
    :param comp_speed: computation speed
    :param msg: the msg extracted and waited to be processed
    """
    time = optimization.computation_time(agent, msg_structure.get_actual_size(msg))
    sleep(time)


logging.basicConfig(level=logging.INFO)


def get_util_msg(a: agent):
    """
    Get the util_table to be sent to the parent and the table to be stored as
    a tuple, (util_table, value_table).
    Each of them are:
    util_table: the maximum utility, axes are the different domain of p and pp
    value_table: the value for max util, axes are the different domain of p and pp
    """

    info = a.agents_info
    # Domain of the parent
    parent_domain = info[a.p]['domain']
    # Calculate the dimensions of the util_table
    # The dimensions of util_table and table_stored will be the same.
    # [ len_of_parent_domain, len_of_pparent_domain...]
    dim_util_msg = [len(parent_domain)] + [len(info[x]['domain']) for x in a.pp]
    dim_util_msg = tuple(dim_util_msg)

    # util_table for utility value, value_table for the chosen value for agent
    util_table = np.empty(dim_util_msg, dtype=object)
    value_table = np.empty(dim_util_msg, dtype=object)

    # [[p_domain],[pp_domain], ...]
    lists = [parent_domain] + [info[x]['domain'] for x in a.pp]

    # [[1,2,...,len p_domain], ...]
    indices = [range(len(parent_domain))] + [range(len(info[x]['domain'])) for x in a.pp]

    # tuple(v1, v2, ...), tuple(index1, index2, ...)
    for item, index in zip(itertools.product(*lists), itertools.product(*indices)):
        max_util = a.max_util
        xi_val = -1
        for xi in a.domain:
            # for each set value of p/parents, choose the with most gain
            util = a.calculate_util(item, xi)
            if util > max_util:
                max_util = util
                xi_val = xi
        util_table[index] = max_util
        value_table[index] = xi_val

    a.table_ant = tuple([a.p] + a.pp)

    return util_table, value_table


def get_util_cube(a: agent):
    """
    Get the utility cube which will be used by a non-leaf node to combine with
    the combined cube it has generated from the util_msgs received from all the
    children.
    :returns
    util_msgs: indices of itself, p, pps: utilities
    dim_util_msg: dims of domains basically
    """

    info = a.agents_info

    # Domain of the parent
    parent_domain = info[a.p]['domain']
    # Calculate the dimensions of the util_msg
    # The dimensions of util_msg and table_stored will be the same.
    # dim_util_msg = [ size_agent_domain, size_pdoomain, size_ppdomain,..]
    dim_util_msg = [len(a.domain)] + [len(parent_domain)] + \
                   [len(info[x]['domain']) for x in a.pp]
    dim_util_msg = tuple(dim_util_msg)
    util_msg = np.empty(dim_util_msg, dtype=object)

    lists = [parent_domain] + [info[x]['domain'] for x in a.pp]
    indices = [range(len(parent_domain))] + \
              [range(len(info[x]['domain'])) for x in a.pp]

    for item, index in zip(itertools.product(*lists), itertools.product(*indices)):
        for i, xi in enumerate(a.domain):
            util = a.calculate_util(item, xi)
            util_msg[(i,) + index] = util

    return util_msg, dim_util_msg


def get_util_cube_pipeline(agent):
    """
    Get the utility cube which will be used by a non-leaf node
    has a utility cube with axis for [pp, p, agent self]

    Dimension order is different
    :returns
    util_msgs: indices of pps, p , self: utilities
    dim_util_msg: dims of domains basically
    """

    util_msg, dim_util_msg = get_util_cube(agent)

    prev = list([agent.id] + [agent.p] + agent.pp)
    reorder = list(agent.pp + [agent.p] + [agent.id])

    util_msg = np.transpose(util_msg, tuple([prev.index(x) for x in reorder]))
    if len(dim_util_msg) > 2:
        dim_util_msg = tuple(list(dim_util_msg[2:]) + [dim_util_msg[1]] + [dim_util_msg[0]])
    else:
        dim_util_msg = [dim_util_msg[1]] + [dim_util_msg[0]]

    return util_msg, dim_util_msg


def util_msg_handler(agent: agent):
    """
    The util_msg_handler routine in the util_msg_prop part; this method
    is run for non-leaf nodes;
    It waits till all the children of this agent have sent their util_msg,
    combines them, and then calculates and sends the util_msg to its parent;
    If this node is the root node, it waits till all the children have sent
    their util_msg, combines these messages, chooses the assignment for itself
    with the optimal utility, and then sends this assignment and optimal utility
    value to all its children and pseudo-children; assumes that the listening
    thread is active;
    given the 'agent' which runs this function.
    """

    # Wait till util_msg from all the children have arrived
    while True:
        all_children_msgs_arrived = True
        for child in agent.c:
            if ('util_msg_' + str(child)) not in agent.msgs:
                all_children_msgs_arrived = False
                break
        if all_children_msgs_arrived:
            break

    util_msgs = []
    for child in sorted(agent.c):
        util_msgs.append(agent.msgs['util_msg_' + str(child)])
    for child in sorted(agent.c):
        util_msgs.append(agent.msgs['pre_util_msg_' + str(child)])

    combined_msg, combined_ant = utility.combine(*util_msgs)

    if agent.slow_processing:
        slow_process(util_msgs, agent.comp_speed)

    # info = agent.agents_info

    if agent.is_root:
        assert combined_ant == (agent.id,)

        # Choose the optimal utility
        utilities = list(combined_msg)
        max_util = max(utilities)
        xi_star = agent.domain[utilities.index(max_util)]
        agent.value = xi_star
        agent.max_util = max_util

        # Send the index of assigned value
        D = {}
        ind = agent.domain.index(xi_star)
        D[agent.id] = ind
        for node in agent.c:
            # agent.udp_send('value_msg_'+str(agent.id), D, node)
            # agent.tcp_send('value_msg_' + str(agent.id), D, node)
            agent.send('value_msg_' + str(agent.id), D, node)
    else:
        util_cube, _ = get_util_cube(agent)

        # Combine the 2 cubes
        combined_cube, cube_ant = utility.combine(
            util_cube, combined_msg,
            tuple([agent.id] + [agent.p] + agent.pp), combined_ant
        )

        # Removing own dimension by taking maximum
        L_ant = list(cube_ant)
        ownid_index = L_ant.index(agent.id)
        msg_to_send = np.maximum.reduce(combined_cube, axis=ownid_index)
        # Ant to send in pre_util_msg
        ant_to_send = cube_ant[:ownid_index] + cube_ant[ownid_index + 1:]

        # Creating the table to store
        cc = combined_cube
        table_shape = list(cc.shape[:])
        del table_shape[ownid_index]
        table_shape = tuple(table_shape)

        table = np.zeros(table_shape, dtype=object)
        cc_rolled = np.rollaxis(cc, ownid_index)
        for i, abc in enumerate(cc_rolled):
            for index, _ in np.ndenumerate(abc):
                if abc[index] == msg_to_send[index]:
                    table[index] = agent.domain[i]
        agent.table = table
        agent.table_ant = ant_to_send

        # Send the assignment-nodeid-tuple

        agent.send('pre_util_msg_' + str(agent.id), ant_to_send, agent.p)
        agent.send('util_msg_' + str(agent.id), msg_to_send, agent.p)


def util_msg_prop(agent: agent):
    agent.logger.info(f"Begin util_msg_prop")

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        # info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), tuple([agent.p] + agent.pp), agent.p)

        # Send 'util_msg_<ownid>'' to parent
        agent.send('util_msg_' + str(agent.id), util_msg, agent.p)

    else:
        util_msg_handler(agent)

    agent.logger.info(f"End util_msg_prop")


def util_msg_handler_split(agent):
    """
    Change the handling of util message from waiting to piece by piece
    """

    # need to wait until all pre_util_msg arrived, need to know the dimensions
    while True:
        all_children_pre_msgs_arrived = True
        for child in agent.c:
            if ('pre_util_msg_' + str(child)) not in agent.msgs:
                all_children_pre_msgs_arrived = False
                break
        if all_children_pre_msgs_arrived:
            break

    pre_msgs = [agent.msgs['pre_util_msg_' + str(child)] for child in sorted(agent.c)]
    merged_ant = utility.merge_ant(pre_msgs)  # the combined set of nodeids for the table sent from two children

    info = agent.agents_info
    info[agent.i]['domain'] = agent.domain

    # the current problem is that it may only have domain info for neighbors, tmp fix
    try:
        l_domains = [info[x]['domain'] for x in merged_ant]
    except KeyError:
        l_domains = [agent.domain for _ in merged_ant]

    domain_ranges = [tuple(range(len(x))) for x in l_domains]  # list of index tuples
    new_array = {indices: [] for indices in itertools.product(*domain_ranges)}

    if len(agent.c) == 2:  # the will wait for 2 piece of infomation
        index_ant1 = [list(merged_ant).index(i) for i in pre_msgs[0]]
        index_ant2 = [list(merged_ant).index(i) for i in pre_msgs[1]]

        while True:
            all_children_msgs_arrived = True
            if sum([len(x) for x in new_array.values()]) < 2 * len(new_array):  # there should be 2 value in each entry
                all_children_msgs_arrived = False
                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info

                    if agent.slow_processing:
                        slow_process(agent, msg)

                    title = msg[0]
                    # is a dict of format {(indices) : util}

                    # add based on the children
                    if title.split("_")[-1] == str(sorted(agent.c)[0]):
                        try:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple([len(info[x]['domain']) for x in
                                                                                pre_msgs[0]]))
                        except KeyError:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple(
                                                                             [len(agent.domain) for _ in pre_msgs[0]]))
                        for i in range(len(sliced_msg)):
                            expand = []
                            for x in range(len(merged_ant)):
                                if x not in index_ant1:
                                    expand.append(tuple(range(len(l_domains[x]))))
                                else:
                                    expand.append((list(sliced_msg.keys())[0][index_ant1.index(x)],))

                            to_add = {x: list(sliced_msg.values())[0] for x in itertools.product(*expand)}

                            for k, v in to_add.items():
                                new_array[k].append(v)

                    elif title.split("_")[-1] == str(sorted(agent.c)[1]):
                        try:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple([len(info[x]['domain']) for x in
                                                                                pre_msgs[1]]))
                        except KeyError:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple(
                                                                             [len(agent.domain) for _ in pre_msgs[1]]))
                        for i in range(len(sliced_msg)):
                            expand = []
                            for x in range(len(merged_ant)):
                                if x not in index_ant2:
                                    expand.append(tuple(range(len(l_domains[x]))))
                                else:
                                    expand.append((list(sliced_msg.keys())[0][index_ant2.index(x)],))

                            to_add = {x: list(sliced_msg.values())[0] for x in itertools.product(*expand)}

                            for k, v in to_add.items():
                                new_array[k].append(v)
            if all_children_msgs_arrived:
                break
    elif len(agent.c) == 1:
        while True:
            all_children_msgs_arrived = True
            if sum([len(x) for x in new_array.values()]) < len(new_array):
                # agent.logger.info(f"{sum([len(x) for x in new_array.values()])} is < {len(new_array)}")
                all_children_msgs_arrived = False
                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info

                    if agent.slow_processing:
                        slow_process(agent, msg)

                    title = msg[0]
                    # is a dict of format {(indices) : util}
                    try:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple(
                                                                         [len(info[x]['domain']) for x in pre_msgs[0]]))
                    except KeyError:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple([len(agent.domain) for _ in pre_msgs[0]]))
                    for k, v in sliced_msg.items():
                        new_array[k].append(v)
            if all_children_msgs_arrived:
                break

    combined_msg = np.zeros([len(x) for x in l_domains])

    for k, v in new_array.items():
        combined_msg[k] = sum(v)

    combined_ant = merged_ant

    # info = agent.agents_info
    if agent.is_root:
        assert combined_ant == (agent.id,)

        # Choose the optimal utility
        utilities = list(combined_msg)
        max_util = max(utilities)
        xi_star = agent.domain[utilities.index(max_util)]
        agent.value = xi_star
        agent.max_util = max_util

        # Send the index of assigned value
        D = {}
        ind = agent.domain.index(xi_star)
        D[agent.id] = ind
        for node in agent.c:
            agent.send('value_msg_' + str(agent.id), D, node)
    else:
        util_cube, _ = get_util_cube(agent)

        # Combine the 2 cubes
        combined_cube, cube_ant = utility.combine(
            util_cube, combined_msg,
            tuple([agent.id] + [agent.p] + agent.pp), combined_ant
        )

        # Removing own dimension by taking maximum
        L_ant = list(cube_ant)
        ownid_index = L_ant.index(agent.id)
        msg_to_send = np.maximum.reduce(combined_cube, axis=ownid_index)
        # Ant to send in pre_util_msg
        ant_to_send = cube_ant[:ownid_index] + cube_ant[ownid_index + 1:]

        # Creating the table to store
        cc = combined_cube
        table_shape = list(cc.shape[:])
        del table_shape[ownid_index]
        table_shape = tuple(table_shape)

        table = np.zeros(table_shape, dtype=object)
        cc_rolled = np.rollaxis(cc, ownid_index)
        for i, abc in enumerate(cc_rolled):
            for index, _ in np.ndenumerate(abc):
                if abc[index] == msg_to_send[index]:
                    table[index] = agent.domain[i]
        agent.table = table
        agent.table_ant = ant_to_send

        # Send the assignment-nodeid-tuple

        agent.send('pre_util_msg_' + str(agent.id), ant_to_send, agent.p)

        sliced_msgs = msg_structure.slice_to_list(agent, msg_to_send)
        # if len(sliced_msgs) > 150 and "UDP" in agent.network_protocol :
        # if False:
        #     for sliced_msg in sliced_msgs[:100]:
        #         agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)
        #         sleep(0.05)
        #     for sliced_msg in sliced_msgs[150:]:
        #         agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)
        #         sleep(0.15)
        # else:
        for sliced_msg in sliced_msgs:
            agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)


def util_msg_prop_split(agent):
    agent.logger.info(f"Begin util_msg_prop_split")

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        # info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), tuple([agent.p] + agent.pp), agent.p)

        # Send 'util_msg_<ownid>'' to parent

        sliced_msgs = msg_structure.slice_to_list(agent, util_msg)
        for sliced_msg in sliced_msgs:
            agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)

    else:
        util_msg_handler_split(agent)

    agent.logger.info(f"End util_msg_prop_split")


def util_msg_handler_list(agent):
    """process
    Change the handling of util message to process list shape but not
    """

    # need to wait until all pre_util_msg arrived, need to know the dimensions
    while True:
        all_children_pre_msgs_arrived = True
        for child in agent.c:
            if ('pre_util_msg_' + str(child)) not in agent.msgs:
                all_children_pre_msgs_arrived = False
                break
        if all_children_pre_msgs_arrived:
            break

    agent.logger.info(f"Start processing util message ALL")

    pre_msgs = [agent.msgs['pre_util_msg_' + str(child)] for child in sorted(agent.c)]
    merged_ant = utility.merge_ant(pre_msgs)  # the combined set of nodeids for the table sent from two children

    info = agent.agents_info
    info[agent.i]['domain'] = agent.domain

    # the current problem is that it may only have domain info for neighbors, tmp fix
    try:
        l_domains = [info[x]['domain'] for x in merged_ant]
    except KeyError:
        l_domains = [agent.domain for _ in merged_ant]

    domain_ranges = [tuple(range(len(x))) for x in l_domains]  # list of index tuples
    new_array = {indices: [] for indices in itertools.product(*domain_ranges)}

    if len(agent.c) == 2:  # the will wait for 2 piece of information
        index_ant1 = [list(merged_ant).index(i) for i in pre_msgs[0]]
        index_ant2 = [list(merged_ant).index(i) for i in pre_msgs[1]]

        while True:
            all_children_msgs_arrived = True
            if sum([len(x) for x in new_array.values()]) < 2 * len(new_array):  # there should be 2 value in each entry
                all_children_msgs_arrived = False
                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info
                    title = msg[0]

                    agent.logger.info(f"Start processing {title}")
                    # is a dict of format {(indices) : util}

                    if agent.slow_processing:
                        slow_process(agent, msg)

                    # add based on the children
                    if title.split("_")[-1] == str(sorted(agent.c)[0]):
                        try:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple([len(info[x]['domain']) for x in
                                                                                pre_msgs[0]]))
                        except KeyError:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple(
                                                                             [len(agent.domain) for _ in pre_msgs[0]]))
                        for i in range(len(sliced_msg)):
                            expand = []
                            for x in range(len(merged_ant)):
                                if x not in index_ant1:
                                    expand.append(tuple(range(len(l_domains[x]))))
                                else:
                                    expand.append((list(sliced_msg.keys())[0][index_ant1.index(x)],))

                            to_add = {x: list(sliced_msg.values())[0] for x in itertools.product(*expand)}

                            for k, v in to_add.items():
                                new_array[k].append(v)

                    elif title.split("_")[-1] == str(sorted(agent.c)[1]):
                        try:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple([len(info[x]['domain']) for x in
                                                                                pre_msgs[1]]))
                        except KeyError:
                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                         tuple(
                                                                             [len(agent.domain) for _ in pre_msgs[1]]))
                        for i in range(len(sliced_msg)):
                            expand = []
                            for x in range(len(merged_ant)):
                                if x not in index_ant2:
                                    expand.append(tuple(range(len(l_domains[x]))))
                                else:
                                    expand.append((list(sliced_msg.keys())[0][index_ant2.index(x)],))

                            to_add = {x: list(sliced_msg.values())[0] for x in itertools.product(*expand)}

                            for k, v in to_add.items():
                                new_array[k].append(v)
            if all_children_msgs_arrived:
                break
    elif len(agent.c) == 1:
        while True:
            all_children_msgs_arrived = True
            if sum([len(x) for x in new_array.values()]) < len(new_array):
                all_children_msgs_arrived = False
                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info

                    title = msg[0]

                    agent.logger.info(f"Start processing {title}")

                    if agent.slow_processing:
                        slow_process(agent, msg)  # slow down processing
                    # is a dict of format {(indices) : util}
                    try:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple(
                                                                         [len(info[x]['domain']) for x in pre_msgs[0]]))
                    except KeyError:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple([len(agent.domain) for _ in pre_msgs[0]]))
                    for k, v in sliced_msg.items():
                        new_array[k].append(v)
            if all_children_msgs_arrived:
                break

    combined_msg = np.zeros([len(x) for x in l_domains])

    agent.logger.info(f"Finish processing util message")

    for k, v in new_array.items():
        combined_msg[k] = sum(v)

    combined_ant = merged_ant

    # info = agent.agents_info
    if agent.is_root:
        assert combined_ant == (agent.id,)

        # Choose the optimal utility
        utilities = list(combined_msg)
        max_util = max(utilities)
        xi_star = agent.domain[utilities.index(max_util)]
        agent.value = xi_star
        agent.max_util = max_util

        # Send the index of assigned value
        D = {}
        ind = agent.domain.index(xi_star)
        D[agent.id] = ind
        for node in agent.c:
            agent.send('value_msg_' + str(agent.id), D, node)
    else:
        util_cube, _ = get_util_cube(agent)

        # Combine the 2 cubes
        combined_cube, cube_ant = utility.combine(
            util_cube, combined_msg,
            tuple([agent.id] + [agent.p] + agent.pp), combined_ant
        )

        # Removing own dimension by taking maximum
        L_ant = list(cube_ant)
        ownid_index = L_ant.index(agent.id)
        msg_to_send = np.maximum.reduce(combined_cube, axis=ownid_index)
        # Ant to send in pre_util_msg
        ant_to_send = cube_ant[:ownid_index] + cube_ant[ownid_index + 1:]

        # Creating the table to store
        cc = combined_cube
        table_shape = list(cc.shape[:])
        del table_shape[ownid_index]
        table_shape = tuple(table_shape)

        table = np.zeros(table_shape, dtype=object)
        cc_rolled = np.rollaxis(cc, ownid_index)
        for i, abc in enumerate(cc_rolled):
            for index, _ in np.ndenumerate(abc):
                if abc[index] == msg_to_send[index]:
                    table[index] = agent.domain[i]
        agent.table = table
        agent.table_ant = ant_to_send

        # Send the assignment-nodeid-tuple

        agent.send('pre_util_msg_' + str(agent.id), ant_to_send, agent.p)

        sliced_msg = msg_structure.table_to_list(msg_to_send)
        agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)


def util_msg_prop_list(agent):
    agent.logger.info(f"Begin util_msg_prop_split_original")

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        # info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), tuple([agent.p] + agent.pp), agent.p)

        # Send 'util_msg_<ownid>'' to parent

        # make table to list
        sliced_msg = msg_structure.table_to_list(util_msg)
        agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)

    else:
        util_msg_handler_list(agent)

    agent.logger.info(f"End util_msg_prop_split")


def util_msg_handler_split_pipeline_root(agent):
    """
    Change the handling of util message from waiting to piece by piece
    """

    # need to wait until all pre_util_msg arrived, need to know the dimensions
    while True:
        all_children_pre_msgs_arrived = True
        for child in agent.c:
            if ('pre_util_msg_' + str(child)) not in agent.msgs:
                all_children_pre_msgs_arrived = False
                break
        if all_children_pre_msgs_arrived:
            break

    pre_msgs = [agent.msgs['pre_util_msg_' + str(child)] for child in sorted(agent.c)]
    merged_ant = utility.merge_ant(pre_msgs)  # the combined set of nodeids for the table sent from two children

    info = agent.agents_info
    info[agent.i]['domain'] = agent.domain

    # the current problem is that it may only have domain info for neighbors, tmp fix
    try:
        l_domains = [info[x]['domain'] for x in merged_ant]
    except KeyError:
        l_domains = [agent.domain for _ in merged_ant]

    domain_ranges = [tuple(range(len(x))) for x in l_domains]  # list of index tuples
    new_array = {indices: [] for indices in itertools.product(*domain_ranges)}

    if len(agent.c) == 2:  # the will wait for 2 piece of infomation
        index_ant1 = [list(merged_ant).index(i) for i in pre_msgs[0]]
        index_ant2 = [list(merged_ant).index(i) for i in pre_msgs[1]]

        while True:
            all_children_msgs_arrived = True
            if sum([len(x) for x in new_array.values()]) < 2 * len(new_array):  # there should be 2 value in each entry
                all_children_msgs_arrived = False
                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info

                    if agent.slow_processing:
                        slow_process(agent, msg)

                    title = msg[0]
                    # is a dict of format {(indices) : util}

                    sliced_msg = msg[1]

                    # add based on the children
                    if title.split("_")[-1] == str(sorted(agent.c)[0]):

                        for i in range(len(sliced_msg)):
                            expand = []
                            for x in range(len(merged_ant)):
                                if x not in index_ant1:
                                    expand.append(tuple(range(len(l_domains[x]))))
                                else:
                                    expand.append((list(sliced_msg.keys())[0][index_ant1.index(x)],))

                            to_add = {x: list(sliced_msg.values())[0] for x in itertools.product(*expand)}

                            for k, v in to_add.items():
                                new_array[k].append(v)

                    elif title.split("_")[-1] == str(sorted(agent.c)[1]):
                        for i in range(len(sliced_msg)):
                            expand = []
                            for x in range(len(merged_ant)):
                                if x not in index_ant2:
                                    expand.append(tuple(range(len(l_domains[x]))))
                                else:
                                    expand.append((list(sliced_msg.keys())[0][index_ant2.index(x)],))

                            to_add = {x: list(sliced_msg.values())[0] for x in itertools.product(*expand)}

                            for k, v in to_add.items():
                                new_array[k].append(v)
            if all_children_msgs_arrived:
                break
    elif len(agent.c) == 1:
        while True:
            all_children_msgs_arrived = True
            if sum([len(x) for x in new_array.values()]) < len(new_array):
                all_children_msgs_arrived = False
                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info

                    if agent.slow_processing:
                        slow_process(agent, msg)

                    [title, sliced_msg] = msg
                    # is a dict of format {(indices) : util}
                    for k, v in sliced_msg.items():
                        new_array[k].append(v)
            if all_children_msgs_arrived:
                break

    combined_msg = np.zeros([len(x) for x in l_domains])

    for k, v in new_array.items():
        combined_msg[k] = sum(v)

    combined_ant = merged_ant

    # info = agent.agents_info
    if agent.is_root:
        assert combined_ant == (agent.id,)

        # Choose the optimal utility
        utilities = list(combined_msg)
        max_util = max(utilities)
        xi_star = agent.domain[utilities.index(max_util)]
        agent.value = xi_star
        agent.max_util = max_util

        # Send the index of assigned value
        D = {}
        ind = agent.domain.index(xi_star)
        D[agent.id] = ind
        for node in agent.c:
            agent.send('value_msg_' + str(agent.id), D, node)
    else:
        util_cube, _ = get_util_cube(agent)

        # Combine the 2 cubes
        combined_cube, cube_ant = utility.combine(
            util_cube, combined_msg,
            tuple([agent.id] + [agent.p] + agent.pp), combined_ant
        )

        # Removing own dimension by taking maximum
        L_ant = list(cube_ant)
        ownid_index = L_ant.index(agent.id)
        msg_to_send = np.maximum.reduce(combined_cube, axis=ownid_index)
        # Ant to send in pre_util_msg
        ant_to_send = cube_ant[:ownid_index] + cube_ant[ownid_index + 1:]

        # Creating the table to store
        cc = combined_cube
        table_shape = list(cc.shape[:])
        del table_shape[ownid_index]
        table_shape = tuple(table_shape)

        table = np.zeros(table_shape, dtype=object)
        cc_rolled = np.rollaxis(cc, ownid_index)
        for i, abc in enumerate(cc_rolled):
            for index, _ in np.ndenumerate(abc):
                if abc[index] == msg_to_send[index]:
                    table[index] = agent.domain[i]
        agent.table = table
        agent.table_ant = ant_to_send

        # Send the assignment-nodeid-tuple

        agent.send('pre_util_msg_' + str(agent.id), ant_to_send, agent.p)

        sliced_msgs = msg_structure.slice_to_list(agent, msg_to_send)
        for sliced_msg in sliced_msgs:
            agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)


def util_msg_handler_split_pipeline(agent):
    """
    Change the handling of util message from waiting to piece by piece
    """
    info = agent.agents_info
    info[agent.i]['domain'] = agent.domain

    if agent.is_root:
        # if agent is the root, it still needs to wait for all msg so no pipeline can be done
        # will si,ply use the old method
        util_msg_handler_split_pipeline_root(agent)
        return

    # utility_cube and utility_cube_ant is for the revolving parts without its children' info
    util_cube, _ = get_util_cube_pipeline(agent)  # now the order of dimension is different with pipeline version
    util_cube_ant = tuple(agent.pp + [agent.p] + [agent.id])

    if len(agent.c) == 1:
        """
        waiting for pre_util_msg
        """

        while True:  # need to wait until pre_util_msg arrived
            if ('pre_util_msg_' + str(agent.c[0])) in agent.msgs:
                break

        pre_msgs = [agent.msgs['pre_util_msg_' + str(child)] for child in sorted(agent.c)]  # a list of tuple
        child_ant = pre_msgs[0]  # set of nodeids for the table sent from the single child
        # reorder_merged_ant = swap(child_ant, child_ant.index(agent.id))  # move this agent's id to the last

        assert child_ant.index(agent.id) == len(child_ant) - 1  # current agent should be the last in list

        try:
            msg_shape = tuple([len(info[x]['domain']) for x in child_ant])
        except KeyError:
            msg_shape = tuple([len(agent.domain) for _ in child_ant])

        # combine_ant = [all other nodeid] + agent.p + agent.id
        combine_ant = set(child_ant) | set(util_cube_ant)
        combine_ant = combine_ant - {agent.p, agent.id}
        combine_ant = list(combine_ant) + [agent.p] + [agent.id]  # [tosend + p + itself]

        agent.send('pre_util_msg_' + str(agent.id), combine_ant[:-1], agent.p)  # send out pre_info as soon as possible
        agent.table_ant = combine_ant[:-1]

        try:
            child_domain_sizes = [len(info[x]['domain']) for x in child_ant]
        except KeyError:
            child_domain_sizes = [len(agent.domain) for _ in child_ant]

        try:
            combine_domain_sizes = [len(info[x]['domain']) for x in combine_ant]
        except KeyError:
            combine_domain_sizes = [len(agent.domain) for _ in combine_ant]

        combine_w_util_cube = np.zeros(shape=tuple(combine_domain_sizes))  # storage

        combine_w_util_cube, tmp_ant = utility.combine(combine_w_util_cube, util_cube, tuple(combine_ant),
                                                       tuple(util_cube_ant))

        trans = tuple([tmp_ant.index(x) for x in combine_ant])
        combine_w_util_cube = np.transpose(combine_w_util_cube, trans)

        util_w_msg_cube = np.copy(combine_w_util_cube)
        # print("combine_w_util_cube", combine_w_util_cube)
        """
        actual piece-wise msg
        """
        # print("msg_shape", msg_shape)
        counter = np.prod(msg_shape)  # how many values should be received
        # print("counter", counter)
        processed_keys = []
        msg_tosend_store = {}

        while True:
            all_children_msgs_arrived = True

            if counter > 0:
                # not all of the info are received
                all_children_msgs_arrived = False

                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info

                    if agent.slow_processing:
                        slow_process(agent, msg)

                    [_, value] = msg  # "util something" , [(indices), [list of value]]

                    # if agent.id == 1:
                    #     print(value)

                    # unflod message to normal format
                    if type(value) == list:
                        counter -= len(value[1])  # minus the number of values get
                        unfold_msg = msg_structure.unfold_sliced_msg(value, msg_shape)
                    elif type(value) == dict:
                        counter -= len(value)  # minus the number of values get
                        unfold_msg = value
                    else:
                        sys.exit("type not supported")

                    # keys will be in natural format, put unfold_msg back to matrix format
                    unfold_msg_array = np.zeros(shape=tuple(child_domain_sizes))
                    for k, v in unfold_msg.items():
                        unfold_msg_array[k] += v

                    # add child info to storage_combine
                    util_w_msg_cube, tmp_ant = \
                        utility.combine(util_w_msg_cube, unfold_msg_array, combine_ant, child_ant)

                    # projection from util_w_msg_cube to combine_cube
                    trans = tuple([tmp_ant.index(x) for x in combine_ant])
                    util_w_msg_cube = np.transpose(util_w_msg_cube, trans)  # reorder the axis according to combine_ant

                    # the different in the value of new array2 and storage cube
                    diff = util_w_msg_cube - combine_w_util_cube

                    # the minimum value in this agent axis column,
                    # if 0.0, indicates the information haven't been received
                    amin = np.amin(diff, axis=len(util_w_msg_cube.shape) - 1)

                    # the maximum value in this agent axis column
                    amax = np.amax(util_w_msg_cube, axis=len(util_w_msg_cube.shape) - 1)

                    # if the minimum in the diff is zero then not received
                    msg_tosend = {k: v for k, v in np.ndenumerate(amax) if amin[k] != 0.0 and k not in processed_keys}
                    # print("msg_tosend", msg_tosend)

                    processed_keys += list(msg_tosend.keys())
                    # print("processed_keys", processed_keys)

                    # print("combine_w_util_cube", combine_w_util_cube)
                    # print("util_w_msg_cube", np.sum(util_w_msg_cube))
                    # print("diff", diff)
                    # print("amax",amax)
                    # print("amin",amin)
                    # print("msg_tosend", msg_tosend, "\n")
                    # print(processed_keys)

                    if len(msg_tosend) > 0:
                        agent.send('util_msg_' + str(agent.id), msg_tosend, agent.p)
                        msg_tosend_store.update(msg_tosend)

            if all_children_msgs_arrived:

                L_ant = list(combine_ant)
                ownid_index = L_ant.index(agent.id)

                cc = util_w_msg_cube
                table_shape = list(cc.shape[:])
                del table_shape[ownid_index]
                table_shape = tuple(table_shape)

                table = np.zeros(table_shape, dtype=object)
                cc_rolled = np.rollaxis(cc, ownid_index)
                for i, abc in enumerate(cc_rolled):
                    for index, _ in np.ndenumerate(abc):
                        if abc[index] == msg_tosend_store[index]:
                            table[index] = agent.domain[i]
                agent.table = table

                break

    elif len(agent.c) == 2:  # the will wait for 2 piece of infomation
        # need to wait until all pre_util_msg arrived, need to know the dimensions
        while True:
            all_children_pre_msgs_arrived = True
            for child in agent.c:
                if ('pre_util_msg_' + str(child)) not in agent.msgs:
                    all_children_pre_msgs_arrived = False
                    break
            if all_children_pre_msgs_arrived:
                break

        pre_msgs = [agent.msgs['pre_util_msg_' + str(child)] for child in sorted(agent.c)]  # a list of tuple
        merged_ant = utility.merge_ant(pre_msgs)  # the combined set of nodeids for the table sent from two children
        reorder_merged_ant = swap(merged_ant, merged_ant.index(agent.id))  # move this agent's id to the last
        children_ant = swap(reorder_merged_ant, merged_ant.index(agent.p), -2)  # move this agent's p to the -2

        # [(agent.c 1 domain sizes), (agent.c domain sizes)]
        try:
            msg_shapes = [tuple(len(info[x]['domain']) for x in ant) for ant in pre_msgs]
        except KeyError:
            msg_shapes = [tuple(len(agent.domain) for _ in ant) for ant in pre_msgs]

        # [other_ids, p_id, this agent.id]
        combine_ant = set(children_ant) | set(util_cube_ant)
        combine_ant = combine_ant - {agent.p, agent.id}
        combine_ant = list(combine_ant) + [agent.p] + [agent.id]  # [tosend + p + itself]

        agent.send('pre_util_msg_' + str(agent.id), combine_ant[:-1], agent.p)
        agent.table_ant = combine_ant[:-1]

        # [domain_sizes for each in combine_ant]
        try:
            combine_domain_sizes = [len(info[x]['domain']) for x in combine_ant]
        except KeyError:
            combine_domain_sizes = [len(agent.domain) for _ in combine_ant]

        # storages
        # ndarray initilize with 0 of shapecombine_domain_sizes
        combine_w_util_cube = np.zeros(shape=tuple(combine_domain_sizes))

        # put cube_util in
        combine_w_util_cube, tmp_ant = utility.combine(combine_w_util_cube, util_cube, tuple(combine_ant),
                                                       tuple(util_cube_ant))
        trans = tuple([tmp_ant.index(x) for x in combine_ant])
        combine_w_util_cube = np.transpose(combine_w_util_cube, trans)

        util_w_msg_cubes = [np.copy(combine_w_util_cube), np.copy(combine_w_util_cube)]  # for each

        """
        actual piece-wise msg
        """
        # print("msg_shape", msg_shape)
        counter = sum([np.prod(msg_shape) for msg_shape in msg_shapes])  # how many values should be received
        # print("counter", counter)
        processed_keys = []  # processed keys for tosend, for keys after combination
        msg_tosend_store = {}

        while True:
            all_children_msgs_arrived = True

            if counter > 0:
                # not all of the info are received
                all_children_msgs_arrived = False

                if len(agent.unprocessed_util) > 0:
                    # actually do the processing

                    msg = agent.unprocessed_util.pop(0)  # a piece of info

                    if agent.slow_processing:
                        slow_process(agent, msg)

                    [title, value] = msg  # "util something" , [(indices), [list of value]]

                    which_child = agent.c.index(int(title.split("_")[-1]))  # 0 if first child, 1 otherwise

                    # unflod message to normal format
                    if type(value) == list:
                        counter -= len(value[1])  # minus the number of values get
                        unfold_msg = msg_structure.unfold_sliced_msg(value, msg_shapes[which_child])
                    elif type(value) == dict:
                        counter -= len(value)  # minus the number of values get
                        unfold_msg = value
                    else:
                        sys.exit("type not supported")

                    # keys will be in natural format, put unfold_msg back to matrix format
                    unfold_msg_array = np.zeros(shape=tuple(msg_shapes[which_child]))
                    for k, v in unfold_msg.items():
                        unfold_msg_array[k] += v

                    # add child info to storage_combine
                    util_w_msg_cubes[which_child], tmp_ant = \
                        utility.combine(util_w_msg_cubes[which_child], unfold_msg_array,
                                        combine_ant, pre_msgs[which_child])

                    # projection from util_w_msg_cube to combine_cube
                    trans = tuple([tmp_ant.index(x) for x in combine_ant])
                    # reorder the axis according to combine_ant
                    util_w_msg_cubes[which_child] = np.transpose(util_w_msg_cubes[which_child], trans)

                    # the different in the value of new array and the util cube
                    diff1 = util_w_msg_cubes[0] - combine_w_util_cube
                    diff2 = util_w_msg_cubes[1] - combine_w_util_cube

                    # the minimum value in this agent axis column,
                    # if 0.0, indicates the information haven't been received
                    amin1 = np.amin(diff1, axis=len(util_w_msg_cubes[0].shape) - 1)
                    amin2 = np.amin(diff2, axis=len(util_w_msg_cubes[1].shape) - 1)

                    # the maximum value in this agent axis column
                    amax = np.amax(util_w_msg_cubes[0] + util_w_msg_cubes[1],
                                   axis=len(util_w_msg_cubes[which_child].shape) - 1)

                    # if the minimum in either diff is zero then not full info received
                    msg_tosend = {k: v for k, v in np.ndenumerate(amax) if amin1[k] != 0.0
                                  and amin2[k] != 0.0
                                  and k not in processed_keys}

                    processed_keys += list(msg_tosend.keys())

                    if len(msg_tosend) > 0:
                        agent.send('util_msg_' + str(agent.id), msg_tosend, agent.p)
                        msg_tosend_store.update(msg_tosend)

            if all_children_msgs_arrived:

                L_ant = list(combine_ant)
                ownid_index = L_ant.index(agent.id)

                cc = util_w_msg_cubes[0] + util_w_msg_cubes[1] - combine_w_util_cube
                table_shape = list(cc.shape[:])
                del table_shape[ownid_index]
                table_shape = tuple(table_shape)

                table = np.zeros(table_shape, dtype=object)
                cc_rolled = np.rollaxis(cc, ownid_index)
                for i, abc in enumerate(cc_rolled):
                    for index, _ in np.ndenumerate(abc):
                        if abc[index] == msg_tosend_store[index]:
                            table[index] = agent.domain[i]
                agent.table = table

                break


def util_msg_prop_split_pipeline(agent):
    """
    for pipeline, the current naive implementation is do optimization at leaf then send them all

    """
    agent.logger.info(f"Begin util_msg_prop_split_pipeline")

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        # info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        list_ant = list(agent.pp + [agent.p])
        util_msg = np.swapaxes(util_msg, 0, -1)  # swap parent's axis to the last(was in 0)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), list_ant, agent.p)

        # Send 'util_msg_<ownid>'' to parent
        sliced_msgs = msg_structure.slice_to_list_pipeline(agent, util_msg)

        for sliced_msg in sliced_msgs:
            agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)

    else:
        util_msg_handler_split_pipeline(agent)

    agent.logger.info(f"End util_msg_prop_split")
