"""
const tp comes from network.py

"""

from network import *


def optimize_size(original_table):
    timw_woOpt = sys.getsizeof(original_table) / tp + comp_time(original_table.shape)


def total_time(original_table, piece_shape: tuple) -> float:
    n_pieces = np.size(original_table) / np.product(piece_shape)
    trans = size_shape(piece_shape) / tp
    comp = comp_time(piece_shape)

    if trans >= comp:
        # transmition takes more time
        return n_pieces * trans + comp
    else:
        return n_pieces * comp + trans


def comp_time(table_shape: tuple) -> float:
    clock_rate = 3 * 10 ** 9  # unit in Hz
    return np.product(table_shape) / clock_rate  # return unit in seconds


def slice(original_table) -> list:
    """
    the method will slice the original table into smaller pieces for faster communication

    :param original_table: either nested list for np.ndarray
    :return: list of list(anchor_index, ndarray)
    """

    sliced_msgs = []
    o_shape = original_table.shape

    return sliced_msgs


def size_shape(table_dim) -> int:
    """
    gives the size in byte by the table dim, size of dim = tuple(a,b,c)
    :param table_dim: a tuple describe the shape of a table
    :return: size in byte
    """
    return 80 + 16 * len(table_dim) + 8 * np.product(table_dim)
