"""
This module implements the functions required by the util_msg_propogation
part of the DPOP algorithm
"""

import numpy as np
import itertools
from time import sleep
from datetime import datetime as dt

import utility
import optimization
import msg_structure

slow_processing = True


def swap(indices: tuple, location: int, dest: int = -1) -> tuple:
    new_indices = list(indices)
    new_indices[dest] = indices[location]
    new_indices[location] = indices[dest]
    return tuple(new_indices)


def slow_process(msg):
    """
    sleep by a certain amount of time based on the size of msg
    :param msg: the msg extracted and waited to be processed
    """
    time = optimization.computation_time(msg_structure.get_actual_size(msg))
    sleep(time)


def get_util_msg(agent):
    """
    Get the util_table to be sent to the parent and the table to be stored as
    a tuple, (util_table, value_table).
    Each of them are:
    util_table: the maximum utility, axes are the different domain of p and pp
    value_table: the value for max util, axes are the different domain of p and pp
    """

    info = agent.agents_info
    # Domain of the parent
    parent_domain = info[agent.p]['domain']
    # Calculate the dimensions of the util_table
    # The dimensions of util_table and table_stored will be the same.
    # [ len_of_parent_domain, len_of_pparent_domain...]
    dim_util_msg = [len(parent_domain)] + [len(info[x]['domain']) for x in agent.pp]
    dim_util_msg = tuple(dim_util_msg)

    # util_table for utility value, value_table for the chosen value for agent
    util_table = np.empty(dim_util_msg, dtype=object)
    value_table = np.empty(dim_util_msg, dtype=object)

    # [[p_domain],[pp_domain], ...]
    lists = [parent_domain] + [info[x]['domain'] for x in agent.pp]

    # [[1,2,...,len p_domain], ...]
    indices = [range(len(parent_domain))] + [range(len(info[x]['domain'])) for x in agent.pp]

    # tuple(v1, v2, ...), tuple(index1, index2, ...)
    for item, index in zip(itertools.product(*lists), itertools.product(*indices)):
        max_util = agent.max_util
        xi_val = -1
        for xi in agent.domain:
            # for each set value of p/parents, choose the with most gain
            util = agent.calculate_util(item, xi)
            if util > max_util:
                max_util = util
                xi_val = xi
        util_table[index] = max_util
        value_table[index] = xi_val

    agent.table_ant = tuple([agent.p] + agent.pp)

    return util_table, value_table


def get_util_cube(agent):
    """
    Get the utility cube which will be used by a non-leaf node to combine with
    the combined cube it has generated from the util_msgs received from all the
    children.
    :returns
    util_msgs: indices of itself, p, pps: utilities
    dim_util_msg: dims of domains basically
    """

    info = agent.agents_info

    # Domain of the parent
    parent_domain = info[agent.p]['domain']
    # Calculate the dimensions of the util_msg
    # The dimensions of util_msg and table_stored will be the same.
    # dim_util_msg = [ size_agent_domain, size_pdoomain, size_ppdomain,..]
    dim_util_msg = [len(agent.domain)] + [len(parent_domain)] + \
                   [len(info[x]['domain']) for x in agent.pp]
    dim_util_msg = tuple(dim_util_msg)
    util_msg = np.empty(dim_util_msg, dtype=object)

    lists = [parent_domain] + [info[x]['domain'] for x in agent.pp]
    indices = [range(len(parent_domain))] + \
              [range(len(info[x]['domain'])) for x in agent.pp]

    for item, index in zip(itertools.product(*lists), itertools.product(*indices)):
        for i, xi in enumerate(agent.domain):
            util = agent.calculate_util(item, xi)
            util_msg[(i,) + index] = util

    return util_msg, dim_util_msg


def util_msg_handler(agent):
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

    info = agent.agents_info

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


def util_msg_prop(agent):
    print(dt.now(), str(agent.id) + ': Begin util_msg_prop')

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), tuple([agent.p] + agent.pp), agent.p)

        # Send 'util_msg_<ownid>'' to parent
        agent.send('util_msg_' + str(agent.id), util_msg, agent.p)

    else:
        util_msg_handler(agent)

    print(dt.now(), str(agent.id) + ': End util_msg_prop')


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

                    if slow_process:
                        slow_process(msg)

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
                                                                             [len(agent.domain) for x in pre_msgs[0]]))
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
                                                                             [len(agent.domain) for x in pre_msgs[1]]))
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

                    if slow_process:
                        slow_process(msg)

                    title = msg[0]
                    # is a dict of format {(indices) : util}
                    try:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple(
                                                                         [len(info[x]['domain']) for x in pre_msgs[0]]))
                    except KeyError:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple([len(agent.domain) for x in pre_msgs[0]]))
                    for k, v in sliced_msg.items():
                        new_array[k].append(v)
            if all_children_msgs_arrived:
                break

    combined_msg = np.zeros([len(x) for x in l_domains])

    for k, v in new_array.items():
        combined_msg[k] = sum(v)

    combined_ant = merged_ant

    info = agent.agents_info
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

        sliced_msgs = msg_structure.slice_to_list(msg_to_send)
        for sliced_msg in sliced_msgs:
            agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)


def util_msg_prop_split(agent):
    print(dt.now(), str(agent.id) + ': Begin util_msg_prop_split')

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), tuple([agent.p] + agent.pp), agent.p)

        # Send 'util_msg_<ownid>'' to parent

        sliced_msgs = msg_structure.slice_to_list(util_msg)
        for sliced_msg in sliced_msgs:
            agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)

    else:
        util_msg_handler_split(agent)

    print(dt.now(), str(agent.id) + ': End util_msg_prop_split')


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

    print(dt.now(), str(agent.id) + f" Start processing util message ALL")

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

                    print(dt.now(), f" {agent.id}: start processing {title}")
                    # is a dict of format {(indices) : util}

                    if slow_processing:
                        slow_process(msg)

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

                    print(dt.now(), f"{agent.id}: start processing {title}")

                    if slow_processing:
                        slow_process(msg)  # slow down processing
                    # is a dict of format {(indices) : util}
                    try:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple(
                                                                         [len(info[x]['domain']) for x in pre_msgs[0]]))
                    except KeyError:
                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1],
                                                                     tuple([len(agent.domain) for x in pre_msgs[0]]))
                    for k, v in sliced_msg.items():
                        new_array[k].append(v)
            if all_children_msgs_arrived:
                break

    combined_msg = np.zeros([len(x) for x in l_domains])

    print(dt.now(), str(agent.id) + f" finish processing util message")

    for k, v in new_array.items():
        combined_msg[k] = sum(v)

    combined_ant = merged_ant

    info = agent.agents_info
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
    print(dt.now(), str(agent.id) + ': Begin util_msg_prop_split_original')

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), tuple([agent.p] + agent.pp), agent.p)

        # Send 'util_msg_<ownid>'' to parent

        # make table to list
        sliced_msg = msg_structure.table_to_list(util_msg)
        agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)

    else:
        util_msg_handler_list(agent)

    print(dt.now(), str(agent.id) + ': End util_msg_prop_split')


def util_msg_handler_split_pipeline(agent):
    """
    Change the handling of util message from waiting to piece by piece
    """
    info = agent.agents_info
    info[agent.i]['domain'] = agent.domain

    if len(agent.c) == 1:
        """
        waiting for pre_util_msg
        """
        # need to wait until pre_util_msg arrived
        while True:
            if ('pre_util_msg_' + str(agent.c[0])) in agent.msgs:
                break

        pre_msgs = [agent.msgs['pre_util_msg_' + str(child)] for child in sorted(agent.c)]  # a list of tuple
        merged_ant = pre_msgs[0]  # set of nodeids for the table sent from the single child
        reorder_merged_ant = swap(merged_ant, merged_ant.index(agent.id))  # move this agent's id to the last

        if len(reorder_merged_ant) > 1:  # ( ant has other agents + agent.p , agent )
            new_ant = reorder_merged_ant[:-1]  # delete this agent
            location = new_ant.index(agent.p)  # index of parent
            reorder_new_ant = swap(new_ant, location)  # move parent to the last

            agent.send('pre_util_msg_' + str(agent.id), reorder_new_ant, agent.p)  # send the pre-util msg

            try:
                l_domains2 = [info[x]['domain'] for x in reorder_new_ant]
            except KeyError:
                l_domains2 = [agent.domain for _ in reorder_new_ant]
            domain_ranges = [tuple(range(len(x))) for x in l_domains2]  # list of index tuples
            new_array2 = {indices: [] for indices in itertools.product(*domain_ranges)}  # storage

            """
            actual piece-wise msg
            """

            while True:
                all_children_msgs_arrived = True

                if sum([len(x) for x in new_array2.values()]) < len(new_array2) * len(
                        agent.domain):  # not all of the info are received
                    all_children_msgs_arrived = False

                    if len(agent.unprocessed_util) > 0:
                        # actually do the processing

                        msg = agent.unprocessed_util.pop(0)  # a piece of info

                        if slow_process:
                            slow_process(msg)

                        title = msg[0]  # "pre_util something"

                        # sliced_msg is a dict of format {(indices) : util}
                        try:
                            shape = tuple([len(info[x]['domain']) for x in pre_msgs[0]])
                        except KeyError:
                            shape = tuple([len(agent.domain) for x in pre_msgs[0]])

                        sliced_msg = msg_structure.unfold_sliced_msg(msg[1], shape)  # keys will be in natural format

                        for k, v in sliced_msg.items():
                            k = k[:-1]
                            new_array2[swap(k, k.index(agent.p))].append(v)  # add all to new array

                        new_msg = {}

                        for k, v in new_array2.items():
                            if len(v) == len(agent.domain):  # enough information is collected
                                new_msg[k] = np.max(v)
                                new_array2.pop(k)  # remove processed from the storage

                        agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)

                if all_children_msgs_arrived:
                    break

        else:  # only this agent

            value_list = {}

            if agent.is_root:  # ignore the other conditions for now
                while True:
                    all_children_msgs_arrived = True

                    if len(value_list) < agent.domain:
                        all_children_msgs_arrived = False

                        if len(agent.unprocessed_util) > 0:
                            # actually do the processing

                            msg = agent.unprocessed_util.pop(0)  # a piece of info

                            if slow_process:
                                slow_process(msg)

                            title = msg[0]  # "pre_util something"

                            # sliced_msg is a dict of format {(indices) : util}
                            try:
                                shape = tuple([len(info[x]['domain']) for x in pre_msgs[0]])
                            except KeyError:
                                shape = tuple([len(agent.domain) for x in pre_msgs[0]])

                            sliced_msg = msg_structure.unfold_sliced_msg(msg[1], shape)

                            for k, v in sliced_msg.items():  # add the msg back to array
                                value_list[k] = v
                    if all_children_msgs_arrived:
                        break

                utilities = value_list.values()
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

        # index of agent id in reorder_merged_ant

        index_ant1 = [list(reorder_merged_ant).index(i) for i in pre_msgs[0]]
        index_ant2 = [list(reorder_merged_ant).index(i) for i in pre_msgs[1]]

        # the current problem is that it may only have domain info for neighbors, tmp fix
        try:
            l_domains = [info[x]['domain'] for x in merged_ant]
        except KeyError:
            l_domains = [agent.domain for _ in merged_ant]

        domain_ranges = [tuple(range(len(x))) for x in l_domains]  # list of index tuples
        new_array = {indices: [] for indices in itertools.product(*domain_ranges)}

    # no more else as leaf-nodes will be dealt with different method


def util_msg_prop_split_pipeline(agent):
    """
    for pipeline, the current naive implementation is do optimization at leaf then send them all

    """
    print(dt.now(), str(agent.id) + ': Begin util_msg_prop_split_pipeline')

    if agent.is_leaf():
        # if agents is leaf, just send the utility messages needed
        # no need to include it self so get_util_msg()

        info = agent.agents_info
        util_msg, agent.table = get_util_msg(agent)

        list_ant = list(agent.pp + [agent.p])
        util_msg = np.swapaxes(util_msg, 0, -1)  # swap parent's axis to the last(was in 0)

        # Send the assignment-nodeid-tuple
        agent.send('pre_util_msg_' + str(agent.id), list_ant, agent.p)

        # Send 'util_msg_<ownid>'' to parent
        sliced_msgs = msg_structure.slice_to_list_pipeline(util_msg)

        for sliced_msg in sliced_msgs:
            agent.send('util_msg_' + str(agent.id), sliced_msg, agent.p)

    else:
        util_msg_handler_split_pipeline(agent)

    print(dt.now(), str(agent.id) + ': End util_msg_prop_split')
