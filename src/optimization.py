import numpy as np
from scipy import optimize

import network
import msg_structure


def optimize_size(agent, original_table: np.array, start_length: int = 1) -> int:
    """
    return the size of smaller pieces based on the computation function and tp
    :param agent:
    :param start_length: a parameter sets the minimum length for the minimizer search
    :param original_table:
    :return: a tuple represents the shape
    """

    if start_length == 1:
        result = [time_with_optimization(agent, original_table, x) for x in
                  np.arange(start_length, original_table.size+1)]
    else:
        result = [time_with_optimization(agent, original_table, x)
                  for x in np.arange(start_length, original_table.size+1, step=start_length)]

    length = np.arange(start_length, original_table.size+1, start_length)[np.argmin(result)]

    return length


def time_with_optimization(agent, original_table: np.array, length: int) -> float:
    """
    calculated the total time spent if apply optimization, there are two conditions, 1, transmission of
    the msg takes more time, 2, computation takes more time.
    :param agent:
    :param original_table:
    :param length:
    :return: the total time calculated based on the shape of pieces
    """
    n_pieces = int(np.size(original_table) / length) + 1
    trans = network.tran_time(agent, msg_structure.size_sliced_msg(original_table.shape, length))
    comp = computation_time(agent, msg_structure.size_sliced_msg(original_table.shape, length))

    if trans >= comp:
        # transmission takes more time
        return n_pieces * trans + comp
    else:
        # computation takes more time
        return n_pieces * comp + trans


def computation_time(agent, sliced_size: int):
    """
    Calculate the estimated time spent
    :param agent:
    :param sliced_size: size in int
    :return:
    """
    # return np.product(table_dim) * length * 10 / clock_rate  # return unit in seconds
    if agent.slow_processing:
        return (6.144387919188346e-06 * sliced_size + 0.017582085621144466) * 1 / agent.comp_speed
    else:
        return 6.144387919188346e-06 * sliced_size + 0.017582085621144466

# def gradient_descent(f, r, step) -> int:
#     """
#     TODO: be complete to speed up the minimizer finding of optimize size
#     :param f:
#     :param limit: the upper limit of the range, by default should be the np.size of original table
#     :param step:
#     :return:
#     """
#
#     size = 1
#
#     return size
