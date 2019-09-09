"""
const tp comes from network.py

"""

import network
import sys
import numpy as np
import itertools
from scipy import optimize
import pickle


def optimize_size(original_table: np.array, tp=network.tp) -> int:
    """
    return the size of smaller pieces based on the computation function and tp
    :param tp: the throughput from network
    :param original_table:
    :return: a tuple represents the shape
    """
    time_woOpt = mem_calculation(original_table) / tp + \
                 comp_time(original_table.shape, original_table.size)

    def improvement(length: int):
        time_wOpt = total_time(original_table, length)

        return (time_woOpt - time_wOpt) / time_woOpt

    v_improv = np.vectorize(improvement)
    result = v_improv(np.arange(1, original_table.size))
    max_improv = max(result)
    length = list(result).index(max_improv)

    return length

    # result = optimize.minimize_scalar(improvement, bounds=(1, original_table.size), method='bounded')
    # if result.success:  # check if solver was successful
    #     length = int(result.x)
    # else:
    #     length = original_table.size
    #
    # return length


def total_time(original_table: np.array, length: int) -> float:
    """
    calculated the total time spent if we want to do the optimization
    :param original_table:
    :param length:
    :return: the total time calculated based on the shape of pieces
    """
    n_pieces = int(np.size(original_table) / length) + 1
    trans = size_sliced_msg(original_table.shape, length) / network.tp
    comp = comp_time(original_table.shape, length)

    if trans >= comp:
        # transmition takes more time
        return n_pieces * trans + comp
    else:
        return n_pieces * comp + trans


def comp_time(table_dim: tuple, length: int):
    clock_rate = 3 * 10 ** 9  # unit in Hz
    return np.product(table_dim) * length / clock_rate  # return unit in seconds


def slice_1d(original_table: np.array, length: int) -> list:
    """
    the method will slice the original table into smaller pieces for faster communication

    :param length: the length for sliced list
    :param original_table: np.ndarray
    :return: list of dict of length length, len(list[0])=length
            each element will have (index of first element), list of continuous
    """

    elements = {i: u for i, u in np.ndenumerate(original_table)}
    index = list(elements.keys())
    n_chuncks = int(len(index) / length)

    chunck_index = [index[x * length: (x + 1) * length] for x in range(n_chuncks)]
    if n_chuncks * length != len(elements):
        chunck_index.append(index[n_chuncks * length:])

    sliced_msgs = [{index: elements[index] for index in chunck} for chunck in chunck_index]

    sliced_msgs = [[list(sliced_msg.keys())[0], list(sliced_msg.values())] for sliced_msg in sliced_msgs]

    return sliced_msgs


def unfold_msg(sliced_msg: list, index_list: list) -> dict:
    """
    Unfold the sliced msg to be a dictionary where each entry is (index) : value
    :param sliced_msg: an element in the output list from the slice_1d()
    :param index_list: a list of index, result generated by generate_index()
    :return: a dict {(index) : value}
    """
    position = index_list.index(sliced_msg[0])  # the index of the first element of the sliced_msg
    sub_index_list = index_list[position: len(sliced_msg[1])]
    return dict(zip(sub_index_list, sliced_msg[1]))


def generate_index(shape: tuple) -> list:
    """
    Given a shape, return the list of index of each element.
    :param shape: (5,4,3)
    :return: a list. such as [(0, 0, 0), (0, 0, 1), (0, 0, 2)...]
    """
    index = [i for i, d in np.ndenumerate(np.zeros(shape))]
    return index


def size_sliced_msg(table_dim: tuple, length: int) -> int:
    """
    gives the size in byte by the table dim, size of dim = tuple(a,b,c)
    :param length: the length of how many elements it contains
    :param table_dim: a tuple describe the shape of a table
    :return: size in byte
    """

    example = [table_dim, list(np.random.randint(100, size=length))]

    return mem_calculation(example)


# For size calculation

def mem_calculation(obj) -> int:
    """
    To better calculated the size used used by a python object, this function returns the size in bytes
    :param ojb: an python object
    :return: size in bytes
    """

    return sys.getsizeof(pickle.dumps(obj))


if __name__ == '__main__':
    table = np.random.randint(100, size=(6, 5, 4))
    # print(size_sliced_msg(table.shape, 10))
    print(optimize_size(table))
