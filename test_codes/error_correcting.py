import numpy as np
import pickle as pkl
import json

ant = (0,1)

table = np.random.randint(10, size=(2,3))

def scramble(s : str):
    l = len(s)
    l_char = list(s)
    chunk_num = l//20

    final = [l_char[i * chunk_num :(i + 1) * chunk_num ] for i in range((len(l_char) + chunk_num - 1) // chunk_num )]
    final


print(table)

print(pkl.dumps(table))

print(list(pkl.dumps(table)))

print(scramble(pkl.dumps(table)))

