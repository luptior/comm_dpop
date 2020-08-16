"""
Date structure for DPOP message, original implementation used multidimensional array, addition data structure is list
based, [(indedx of first element), [sequential values from ndarray]]

"""
import logging

import numpy as np
import sys
import pickle

import optimization
import agent

logger = logging.getLogger("msg_structure")


def slice_to_list_pipeline(a: agent, original_table: np.array) -> list:
    """
    now add the minimum of length into consideration

    :param a: type agent
    :param original_table: np.ndarray
    :return: list of dict of length length, len(list[0])=length
            each element will have (index of first element), list of continuous
    """

    step = original_table.shape[-1]  # use the last column which corresponds to the agent this message is sent to

    # optimization comes into play
    length = optimization.optimize_size(a, original_table, step)

    elements = {i: u for i, u in np.ndenumerate(original_table)}
    index = list(elements.keys())
    n_chunks = int(len(index) / length)

    chunk_index = [index[x * length: (x + 1) * length] for x in range(n_chunks)]
    if n_chunks * length != len(elements):
        chunk_index.append(index[n_chunks * length:])

    sliced_msgs = [{index: elements[index] for index in chunk} for chunk in chunk_index]

    sliced_msgs = [[list(sliced_msg.keys())[0], list(sliced_msg.values())] for sliced_msg in sliced_msgs]

    return sliced_msgs


def slice_to_list(a: agent, original_table: np.array) -> list:
    """
    the method will slice the original table into smaller pieces for faster communication
    :param a:
    :param original_table: np.ndarray
    :return: list of dict of length length, len(list[0])=length
            each element will have (index of first element), list of continuous
    """

    # optimization comes into play
    if "UDP" in a.network_protocol  and isinstance(a, agent.SplitAgent) or isinstance(a, agent.PipelineAgent):
        # split is necessary but no need for optimization
        # serialized = serialize(title, np.random.randint(0, 100, size=(7500,)))
        # get_actual_size(serialized)
        length = 1472

        if "FEC" in a.network_protocol: # further limit the packet size
            length = length - 20

        # the first frame can carry up to 1472 bytes of UDP data that is, 1500 (MTU of Ethernet) minus 20 bytes of IPv4
        # header, minus 8 bytes of UDP header.
    else:
        length = optimization.optimize_size(a, original_table)

    elements = {i: u for i, u in np.ndenumerate(original_table)}
    index = list(elements.keys())
    n_chunks = int(len(index) / length)

    chunk_index = [index[x * length: (x + 1) * length] for x in range(n_chunks)]
    if n_chunks * length != len(elements):
        chunk_index.append(index[n_chunks * length:])

    sliced_msgs = [{index: elements[index] for index in chunk} for chunk in chunk_index]

    sliced_msgs = [[list(sliced_msg.keys())[0], list(sliced_msg.values())] for sliced_msg in sliced_msgs]

    return sliced_msgs


def table_to_list(original_table: np.array) -> list:
    """
    the method will slice the original table into smaller pieces for faster communication

    :param original_table: np.ndarray
    :return: list of dict of length length, len(list[0])=length
            each element will have (index of first element), list of continuous
    """

    elements = {i: int(u) for i, u in np.ndenumerate(original_table)}

    return [list(elements.keys())[0], list(elements.values())]


def unfold_sliced_msg(sliced_msg: list, shape: tuple) -> dict:
    """
    Unfold the sliced msg to be a dictionary where each entry is (index) : value
    :param sliced_msg: an element in the output list from the sliced_msg
    :param shape: a tuple
    :return: a dict {(index) : value}
    """
    index_list = list(np.ndindex(shape))

    try:
        position = index_list.index(sliced_msg[0])  # the index of the first element of the sliced_msg
    except ValueError:
        sliced_msg = sliced_msg[0]
        try:
            position = index_list.index(sliced_msg[0])
        except IndexError:
            logger.error(sliced_msg)
            return
    sub_index_list = index_list[position: position + len(sliced_msg[1])]
    return dict(zip(sub_index_list, sliced_msg[1]))


def size_sliced_msg(table_dim: tuple, length: int) -> int:
    """
    gives the size in byte by the table dim, size of dim = tuple(a,b,c)
    :param length: the length of how many elements it contains
    :param table_dim: a tuple describe the shape of a table
    :return: size in byte
    """

    example = [table_dim, np.random.random()]

    return get_actual_size(example) + 8 * (length - 1)


def get_actual_size(obj: object) -> int:
    """
    To get the actual size used used by a python object instead of pointers,
    this function first transform the object into pickles form, then returns the size in bytes

    :param obj: an python object
    :return: size in bytes
    """

    return sys.getsizeof(pickle.dumps(obj))
