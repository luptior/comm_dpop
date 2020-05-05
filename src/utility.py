"""This module contains utility functions that are used by other modules."""

import collections
import pickle
from time import sleep
import sys
import socket
import numpy as np

import properties as prop
from network_optimize import *

from reedsolo import RSCodec
import RSCoding

Relatives = collections.namedtuple('Relatives', 'parent pseudoparents children pseudochildren')


def get_agents_info(filepath:str) -> dict:
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


def combine(*args):
    """Return the combined array, given n numpy arrays and their corresponding
    n assignment-nodeid-tuples ('ants')."""

    largs = len(args)
    arrays = args[:int(largs / 2)] # list of actual util tables
    ants = args[int(largs / 2):] # list of [p, pps]

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
    merged_ant = merge_ant(ants)

    merged_array, _ = expand(arrays[0], ants[0], merged_ant, new_shape)
    for array, ant in zip(arrays[1:], ants[1:]):
        new_array, _ = expand(array, ant, merged_ant, new_shape)
        merged_array = merged_array + new_array

    return merged_array, merged_ant


def merge_ant(ants) -> tuple:
    """
    :param ants: a list of two lists of p and pps from children
    :return: a tuple of non-repeated p and ppm sorted
    """
    # Calculate the merged ant,
    merged_ant = set()
    for ant in ants:
        merged_ant = merged_ant | set(ant)
    merged_ant = tuple(sorted(tuple(merged_ant)))

    return merged_ant


def expand(array, ant, new_ant, new_shape):
    """Return the new numpy array after expanding it so that its ant changes
    from 'ant' to 'new_ant'. The value of the new elements created will be
    initialized to 0."""

    # The values of the nodeids in ant and new_ant must be sorted.
    # Insertion sort is used as there is already an inbuilt function in numpy
    # to swap axes.

    # sort the ant sort array based on it
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

    while i != len(new_ant):
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
    return a, ant


def add_dims(array, ant, index, nodeid, depth):
    """
    Return a numpy array with an additional dimension in the place of index.
    The values of all additional elements created are 0. The depth of the
    'nodeid' is given by 'depth'.
    :param array: original data array
    :param ant: corresponding nodeids for original data array
    :param index: where should the additional axis be added
    :param nodeid: the added dim's corresponded nodeid
    :param depth: depth for the added dim
    :return: a numpy array with an additional dimension in the place of index.
    """

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
    return np.product(S)


def element_projection(agent, ants:list,  new_entry):
    """
    :param ants:  The ants for the two data entry
    :param new_entry:
    :return:
    """

    merged_ant=merge_ant(ants)

    if len(ants) == 2 :
        # this projection involves array from 2 children
        shared_ax = (set(ants[0]) & set(ants[1]))[0]
        shared_id = list(merged_ant).index(shared_ax)
        id1 = ants[0].index(shared_ax)
        id2 = ants[2].index(shared_ax)





