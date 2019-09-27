import numpy as np
import sys
import pickle

import optimization


def slice_to_list(original_table: np.array) -> list:
    """
    the method will slice the original table into smaller pieces for faster communication
    :param original_table: np.ndarray
    :return: list of dict of length length, len(list[0])=length
            each element will have (index of first element), list of continuous
    """

    # optimization comes into play
    length = optimization.optimize_size(original_table)

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

    :param length: the length for sliced list
    :param original_table: np.ndarray
    :return: list of dict of length length, len(list[0])=length
            each element will have (index of first element), list of continuous
    """
    length = np.size(original_table)

    elements = {i: u for i, u in np.ndenumerate(original_table)}
    index = list(elements.keys())
    n_chunks = int(len(index) / length)

    chunk_index = [index[x * length: (x + 1) * length] for x in range(n_chunks)]
    if n_chunks * length != len(elements):
        chunk_index.append(index[n_chunks * length:])

    sliced_msgs = [{index: elements[index] for index in chunck} for chunck in chunk_index]

    sliced_msgs = [[list(sliced_msg.keys())[0], list(sliced_msg.values())] for sliced_msg in sliced_msgs]

    return sliced_msgs


def unfold_sliced_msg(sliced_msg: list, shape: tuple) -> dict:
    """
    Unfold the sliced msg to be a dictionary where each entry is (index) : value
    :param sliced_msg: an element in the output list from the slice_1d()
    :param shape: a tuple
    :return: a dict {(index) : value}
    """
    index_list = list(np.ndindex(shape))

    try:
        position = index_list.index(sliced_msg[0])  # the index of the first element of the sliced_msg
    except ValueError:
        sliced_msg = sliced_msg[0]
        position = index_list.index(sliced_msg[0])
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
