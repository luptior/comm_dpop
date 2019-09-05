"""
const tp comes from network.py

"""

import network
import sys
import numpy as np
from scipy import optimize


def optimize_size(original_table, tp=network.tp) -> int:
    """
    return the size of smaller pieces based on the computation function and tp
    :param tp: the throughput from network
    :param original_table:
    :return: a tuple represents the shape
    """
    time_woOpt = sys.getsizeof(original_table) / tp + comp_time(original_table.shape)

    def improvement(length):
        package_size = length

        return
    result = optimize.minimize_scalar(improvement())
    if result.success:  # check if solver was successful
        length = int(result.x)
    else :
        length = np.size(original_table)

    return length


def total_time(original_table, piece_shape: tuple) -> float:
    """
    :param original_table:
    :param piece_shape:
    :return: the total time calculated based on the shape of pieces
    """
    n_pieces = np.size(original_table) / np.product(piece_shape)
    trans = size_shape(piece_shape) / network.tp
    comp = comp_time(piece_shape)

    if trans >= comp:
        # transmition takes more time
        return n_pieces * trans + comp
    else:
        return n_pieces * comp + trans


def comp_time(table_shape: tuple) -> float:
    clock_rate = 3 * 10 ** 9  # unit in Hz
    return np.product(table_shape) / clock_rate  # return unit in seconds


def slice_1d(original_table: np.array, length) -> list:
    """
    the method will slice the original table into smaller pieces for faster communication

    :param original_table: np.ndarray
    :return: list of dict of length length, len(list[0])=length
    """

    elements = {i: u for i, u in np.ndenumerate(original_table)}
    index = [x for x in elements.keys()]
    n_chuncks = int(len(index) / length)

    chunck_index = [index[x * length: (x + 1) * length] for x in range(n_chuncks)]
    chunck_index.append(index[n_chuncks * length:])

    sliced_msgs = [{index: elements[index] for index in chunck} for chunck in chunck_index]

    return sliced_msgs


def size_shape(table_dim) -> int:
    """
    gives the size in byte by the table dim, size of dim = tuple(a,b,c)
    :param table_dim: a tuple describe the shape of a table
    :return: size in byte
    """
    return 80 + 16 * len(table_dim) + 8 * np.product(table_dim)
