import numpy as np
from scipy import optimize

import network
import util_msg_prop
import msg_structure

split_processing = False
computation_speed = 30


def optimize_size(original_table: np.array, start_length: int = 1) -> int:
    """
    return the size of smaller pieces based on the computation function and tp
    :param start_length: a parameter sets the minimum length for the minimizer search
    :param original_table:
    :return: a tuple represents the shape
    """

    if start_length == 1:
        result = [time_with_optimization(original_table, x) for x in np.arange(start_length, original_table.size)]
    else:
        result = [time_with_optimization(original_table, x)
                  for x in np.arange(start_length, original_table.size, start_length)]

    max_improve = min(result)
    length = np.arange(start_length, original_table.size, start_length)[result.index(max_improve)]
    return length


def optimize_size2(original_table: np.array) -> int:
    """
    where i tried to add gradient descent
    :param original_table:
    :return: a tuple represents the shape
    """
    # if np.size(original_table) < 100:
    #     test_range = np.arange(1, original_table.size)
    # else:
    #     test_range = list(np.arange(1, 100)) + \
    #                  list(np.arange(100, original_table.size, 2*int(np.log10(np.size(original_table)))))

    func = lambda x: time_with_optimization(original_table, x)
    result = optimize.minimize(func, np.array(np.size(original_table) / 2))
    print(result)
    result = int(result)

    return result


def time_with_optimization(original_table: np.array, length: int) -> float:
    """
    calculated the total time spent if apply optimization, there are two conditions, 1, transmission of
    the msg takes more time, 2, computation takes more time.
    :param original_table:
    :param length:
    :return: the total time calculated based on the shape of pieces
    """
    n_pieces = int(np.size(original_table) / length) + 1
    trans = network.tran_time(msg_structure.size_sliced_msg(original_table.shape, length))
    comp = computation_time(msg_structure.size_sliced_msg(original_table.shape, length))

    if trans >= comp:
        # transmission takes more time
        return n_pieces * trans + comp
    else:
        # computation takes more time
        return n_pieces * comp + trans


def computation_time(sliced_size: int, clock_rate: int = 3 * 10 ** 9):
    """
    Calculate the estimated time spent
    :param sliced_size: size in int
    :param clock_rate: need to be calculated based on local machine, currently not implemented
    :return:
    """
    # return np.product(table_dim) * length * 10 / clock_rate  # return unit in seconds
    if util_msg_prop.slow_processing:
        return (6.144387919188346e-06 * sliced_size + 0.017582085621144466) * computation_speed
    else:
        return 6.144387919188346e-06 * sliced_size + 0.017582085621144466


def gradient_descent(f, r, step) -> int:
    """
    TODO: be complete to speed up the minimizer finding of optimize size
    :param f:
    :param limit: the upper limit of the range, by default should be the np.size of original table
    :param step:
    :return:
    """

    size = 1



    return size
