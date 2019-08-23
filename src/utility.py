"""This module contains utility functions that are used by other modules."""

import collections
import pickle
from time import sleep
import sys
import socket
import numpy as np

from network_optimize import *

Relatives = collections.namedtuple('Relatives', 'parent pseudoparents children pseudochildren')


def draw_graph(graph, pstree):
    """Draw the tree structure, given a 'graph' and its 'pstree'."""
    raise NotImplementedError


def get_agents_info(filepath):
    """
    Return a dict with that has all the information extracted from a file like
    'agents.txt'.
    """

    f = open(filepath)
    agents_info = {}
    for line in f:
        if line.split() == [] or line[0] == '#':
            continue
        entries = dict([tuple(entry.split("=")) for entry in line.split()])
        id = int(entries['id'])
        del entries['id']
        agents_info[id] = entries
    return agents_info


def listen_func(msgs, sock, agent):
    """
    Continuously listens on the IP and Port specified in 'sock', and stores the
    messages in the dict 'msgs', until an 'exit' message is received. See
    comments in the source code for more information.
    """

    if agent == None:
        agent_id = 'No agent'
    else:
        agent_id = agent.id
    print(str(agent_id) + ': Begin listen_func')

    while True:
        # The 'data' which is received should be the pickled string
        # representation of a tuple.
        # The first element of the tuple should be the data title, a name given
        # to describe the data.
        # This first element will become the key of the 'msgs' dict.
        # The second element should be the actual data to be passed.
        # Loop ends when an exit message is sent.

        # UDP
        # data, addr = sock.recvfrom(65536)
        # udata = pickle.loads(data) # Unpickled data

        # TCP
        connectionSocket, addr = sock.accept()

        total_data = []
        while True:
            data = connectionSocket.recv(4096)
            if not data:
                break
            total_data.append(data)
        data = b''.join(total_data)

        """
        the optimization comes into play
        """
        size = sys.getsizeof(data)

        sleep(tran_time(size)/1000.)

        udata = pickle.loads(data)  # Unpickled data



        msgs[udata[0]] = udata[1]
        print(str(agent_id) + ': Msg received, size is ' + str(len(data)) + " bytes\n" + udata[0] + ": " + str(udata[1]))
        if str(udata[1]) == "exit":
            print(str(agent_id) + ': End listen_func')
            return


def combine(*args):
    """Return the combined array, given n numpy arrays and their corresponding
    n assignment-nodeid-tuples ('ants')."""

    largs = len(args)
    arrays = args[:int(largs / 2)]
    ants = args[int(largs / 2):]

    # Calculate the new shape
    D = {}
    for arr, ant in zip(arrays, ants):
        shape = arr.shape
        for nodeid, depth in zip(ant, shape):
            if nodeid in D:
                continue
            else:
                D[nodeid] = depth
    new_shape = tuple([D[key] for key in sorted(D)])

    # Calculate the merged ant
    merged_ant = set()
    for ant in ants:
        merged_ant = merged_ant | set(ant)
    merged_ant = tuple(sorted(tuple(merged_ant)))

    merged_array, _ = expand(arrays[0], ants[0], merged_ant, new_shape)
    for array, ant in zip(arrays[1:], ants[1:]):
        new_array, _ = expand(array, ant, merged_ant, new_shape)
        merged_array += new_array

    return merged_array, merged_ant


def expand(array, ant, new_ant, new_shape):
    """Return the new numpy array after expanding it so that its ant changes
    from 'ant' to 'new_ant'. The value of the new elements created will be
    initialized to 0."""

    # The values of the nodeids in ant and new_ant must be sorted.
    # Insertion sort is used as there is already an inbuilt function in numpy
    # to swap axes.
    ant = list(ant)
    for j in range(len(ant) - 1):
        i_min = j
        for i in range(j + 1, len(ant)):
            if ant[i] < ant[i_min]:
                i_min = i

        if i_min != j:
            array = np.swapaxes(array, i_min, j)
            ant[j], ant[i_min] = ant[i_min], ant[j]
    ant = tuple(ant)

    a = array.copy()
    x = y = -1
    i = j = 0
    end_of_ant_reached = False

    while (i != len(new_ant)):
        x = new_ant[i]
        try:
            y = ant[j]
        except:
            end_of_ant_reached = True

        if x < y:
            a, ant = add_dims(a, ant, j, x, new_shape[i])
            i += 1
            j += 1
            continue
        elif x > y:
            if not end_of_ant_reached:
                j += 1
            else:
                a, ant = add_dims(a, ant, j, x, new_shape[i])
                i += 1
                j += 1
            continue
        else:  # x == y
            i += 1
            j += 1
            continue

    # Checking if ant has changed properly
    assert ant == new_ant
    return (a, ant)


def add_dims(array, ant, index, nodeid, depth):
    """Return a numpy array with an additional dimension in the place of index.
    The values of all additional elements created are 0. The depth of the 
    'nodeid' is given by 'depth'."""

    assert ant == tuple(sorted(ant))

    a = array.copy()
    a = np.expand_dims(a, axis=index)
    new_a = a
    for _ in range(depth - 1):
        new_a = np.concatenate((new_a, a), axis=index)
    new_ant = list(ant)
    new_ant.insert(index, nodeid)
    new_ant = tuple(new_ant)
    return new_a, new_ant


def prod(S):
    """Returns the product of all elements in a sequence S."""

    product = 1
    for i in S:
        product = product * i
    return product
