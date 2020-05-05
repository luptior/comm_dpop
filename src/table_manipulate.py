import numpy as np
import pandas as pd

import msg_structure
import optimization


def reorder_list(entry_1, entry_2):
    """
    :param entry_1: ( )
    :param entry_2:
    :return:
    """

    [(0, 0), ]


def reorder_table(pre_1: list, pre_2: list, pre_util_1: list, pre_util_2: list, t1: np.ndarray, t2: np.ndarray):
    """

    :param pre_1: contains agent names
    :param pre_2: contains agent names
    :param pre_util_1: contains agent ids
    :param pre_util_2: contains agent ids
    :param t1: the actual utility table
    :param t2: the actual utility table
    :return:
    """
    shared_id = list(set(pre_util_1) & set(pre_util_2))[0]
    shared_index1 = pre_util_1.index(shared_id)
    shared_index2 = pre_util_2.index(shared_id)

    reordered_pre_1 = pre_1.copy()
    reordered_pre_1[-1] = pre_1[shared_index1]
    reordered_pre_1[shared_index1] = pre_1[-1]
    reordered_pre_util_1 = pre_util_1.copy()
    reordered_pre_util_1[-1] = pre_util_1[shared_index1]
    reordered_pre_util_1[shared_index1] = pre_util_1[-1]
    reordered_t1 = np.swapaxes(t1, -1, shared_index1)

    reordered_pre_2 = pre_2.copy()
    reordered_pre_2[-1] = pre_2[shared_index2]
    reordered_pre_2[shared_index2] = pre_2[-1]
    reordered_pre_util_2 = pre_util_2.copy()
    reordered_pre_util_2[-1] = pre_util_2[shared_index2]
    reordered_pre_util_2[shared_index2] = pre_util_2[-1]
    reordered_t2 = np.swapaxes(t2, -1, shared_index2)

    return reordered_pre_1, reordered_pre_2, reordered_pre_util_1, reordered_pre_util_2, reordered_t1, reordered_t2


if __name__ == '__main__':
    pre_1 = ["a1", "a2", "a3"]
    pre_util_1 = [1, 2, 3]
    pre_2 = ["a3", "a4"]
    pre_util_2 = [3, 4]

    t1 = np.random.randint(200, size=(3, 3, 3))
    t2 = np.random.randint(200, size=(3, 3))

    reordered_pre_1, reordered_pre_2, reordered_pre_util_1, reordered_pre_util_2, reordered_t1, reordered_t2 = \
        reorder_table(pre_1, pre_2, pre_util_1, pre_util_2, t1, t2)

    # print(pre_2)
    # print(pre_util_2)
    # for x in msg_structure.slice_to_list(t2):
    #     print(x)
    #
    # print(reordered_pre_2)
    # print(reordered_pre_util_2)
    # for x in msg_structure.slice_to_list(reordered_t2):
    #     print(x)
