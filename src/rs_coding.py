"""This module contains utility functions that supports Reed Solomon Coding."""

import logging
import pickle

from reedsolo import RSCodec, ReedSolomonError

import numpy as np

import datastruct

logger = logging.getLogger("RSCoding")


# Supoorts Reed Soloomon codes

def example():
    rsc = RSCodec(10)

    # Encoding
    raw_list = rsc.encode([1, 2, 3, 4])
    print(raw_list)
    # bytearray(b'\x01\x02\x03\x04,\x9d\x1c+=\xf8h\xfa\x98M')
    byte_array = rsc.encode(bytearray([1, 2, 3, 4]))
    print(byte_array)
    # bytearray(b'\x01\x02\x03\x04,\x9d\x1c+=\xf8h\xfa\x98M')
    # will generate similar result

    # or rsc.encode('hello world'.encode("utf-8"))
    b_str = rsc.encode(b'hello world')
    print(b_str)
    # bytearray(b'hello world\xed%T\xc4\xfd\xfd\x89\xf3\xa8\xaa')

    # Note that chunking is supported transparently to encode any string length.

    # Decoding (repairing)
    print(rsc.decode(b'hello world\xed%T\xc4\xfd\xfd\x89\xf3\xa8\xaa')[0])
    print(rsc.decode(b'heXlo worXd\xed%T\xc4\xfdX\x89\xf3\xa8\xaa')[0])  # 3 errors
    print(rsc.decode(b'hXXXo worXd\xed%T\xc4\xfdX\x89\xf3\xa8\xaa')[0])  # 5 errors
    try:
        rsc.decode(b'hXXXo worXd\xed%T\xc4\xfdXX\xf3\xa8\xaa')[0]  # 6 errors - fail
    except ReedSolomonError:
        print("error happened")


# for the combined messages
def deserialize(input: bytearray, rsc: RSCodec = RSCodec(10), datatype="int64"):
    combined = rsc.decode(input)[0]
    # symbol
    combined_decoded = combined.split(b"\tab")
    # [title, shape, actual data]
    title = combined_decoded[0].decode()
    message = pickle.loads(combined_decoded[1])

    return title, message

    # shape = np.frombuffer(combined_decoded[1], "int64")
    # shape = np.frombuffer(combined_decoded[1].encode(), "int64")

    # if title == "ACK":
    #     return title, combined_decoded[2].decode("utf-8")
    #
    # data = np.frombuffer(combined_decoded[2], datatype)
    #
    # if "ptinfo" in title:
    #     return title, load_relatives(data)
    # elif "domain_" in title or "neighbors_" in title:
    #     return title, list(data)
    # elif "pre_util_msg_" in title:
    #     return title, tuple(data)
    # elif "value_msg_" in title:
    #     return title, load_dict(data)
    # elif "util_msg_" == title[:9]:
    #     # TODO: a more robust way to distinguish these 2
    #     if np.prod(shape) == len(data):
    #         # pure list no split, product of shape = total elements #
    #         if len(shape) == 1:
    #             return title, load_dict(data)
    #         else:
    #             return title, data.reshape(shape)
    #     else:
    #         # split list, product of shape != total elements #
    #         # k = data[:np.prod(shape)]
    #         return title, [tuple(shape), list(data)]
    # else:
    #     logger.error(f"not supportd input: {title}  {type(data)}")
    #     raise Exception(f"not supportd input {title}  {type(data)}")


def serialize(title: str, message, rsc: RSCodec = RSCodec(10)) -> bytearray:

    # if "util_msg_" == title[:9] and isinstance(message, np.ndarray):
    #     # original version of util message
    #     message = message.astype(int)
    #     shape = np.asarray(message.shape, dtype="int64")
    #     b = message.tobytes()
    # elif "util_msg_" == title[:9] and isinstance(message, dict):
    #     # dict version of the util message, used by pipeline
    #     # data = dump_dict(message)
    #     shape = np.asarray(len(message), dtype="int64")
    #     b = pickle.dumps(message)
    # elif "util_msg_" == title[:9] and isinstance(message[0], tuple):
    #     # list version of the util message
    #     k = list(message[0])
    #     v = list(message[1])
    #     shape = np.asarray(k, dtype="int64")
    #     b = np.asarray(v, dtype="int64").tobytes()
    # elif "pre_util_msg_" == title[:13] or "neighbors_" in title or "domain_" in title and \
    #         (isinstance(message, list) or isinstance(message, tuple)):
    #     # for the pre_util_msg_, contain should either be list or tuple
    #     shape = np.asarray(len(message))
    #     b = np.asarray(message, dtype="int64").tobytes()
    # elif "ptinfo" in title and isinstance(message, datastruct.Relatives):
    #     # ptinfo
    #     data = dump_relatives(message)
    #     shape = np.asarray(len(data), dtype="int64")
    #     b = np.asarray(data, dtype="int64").tobytes()
    # elif "value_msg_" in title and isinstance(message, dict):
    #     # for value msg, in dict format
    #     data = dump_dict(message)
    #     shape = np.asarray(len(data), dtype="int64")
    #     b = np.asarray(data, dtype="int64").tobytes()
    # elif "ACK" in title:
    #     # message should be just str
    #     b = data = message.encode("utf-8")
    #     shape = np.asarray(len(data), dtype="int64")
    # else:
    #     logger.error(f"not supportd input: {title}  {message} {type(message)}")
    #     raise Exception(f"not supportd input {title} {type(message)} {message}")



    # combined_str = title.encode() + b"\tab" + shape.tobytes() + b"\tab" + b

    combined_str = title.encode() + b"\tab" + pickle.dumps(message)

    return rsc.encode(combined_str)


def load_dict(l: list) -> dict:
    if len(l) % 2 == 0:
        d = {int(l[2 * i]): int(l[2 * i + 1]) for i in range(len(l) // 2)}
    else:
        logger.error(f"list input l is not with correct length: {len(l)}")
        raise Exception(f"list input l is not with correct length: {len(l)}, {l[:10] if len(l) > 10 else l}")
    return d


def dump_dict(d: dict) -> list:
    # b = b""
    # for k, v in enumerate(d):
    #     b += bytearray(str(k), "utf-8") + b";"
    #     b += bytearray(str(v), "utf-8") + b";"
    # b = b[:-1]  # minus the last b";"

    l = []
    for k, v in d.items():
        l += [k, v]
    return l


def load_relatives(l) -> datastruct.Relatives:
    if not isinstance(l, list):
        l = list(l)
    index = l[:3]
    values = l[3:]

    r = datastruct.Relatives(int(values[0]),
                          [int(x) for x in values[1:index[1]]],
                          [int(x) for x in values[index[1]:index[2]]],
                          [int(x) for x in values[index[2]:]])
    return r


def dump_relatives(relatives: datastruct.Relatives) -> list:
    # dump relatives type to a list
    index = [1, len(relatives.pseudoparents), len(relatives.children)]
    index2 = []
    for i in range(3):
        index2.append(sum(index[:i + 1]))
    l = index2

    l += [relatives.parent] + relatives.pseudoparents + relatives.children + relatives.pseudochildren

    return l


def test_serialize():
    rsc = RSCodec(10)  # 10 ecc symbols\
    # rsc2 = RSCodec(10) # another
    shape = (10, 10, 10)
    #
    #
    input_array = np.random.randint(1000, size=shape)
    # comparison =  input_array == deserilze(rsc, serilze(rsc, input_array), shape)
    # equal_arrays = comparison.all()
    # print(equal_arrays)
    #
    # comparison = input_array == deserilze(rsc2, serilze(rsc, input_array), shape)
    # print(equal_arrays)
    #
    # input_array = np.random.random(size=shape)
    # comparison =  input_array == deserilze(rsc, serilze(rsc, input_array), shape, "float")
    # equal_arrays = comparison.all()
    # print(equal_arrays)

    # serialized = serialize( title="ssss", input_array = input_array)
    serialized = serialize(title="util_msg_1", message=input_array)

    deserialized = deserialize(serialized)

    print(deserialized[1])
    # print(input_array)
    # comparison = input_array == deserialized[1]
    comparison = input_array == deserialized[1]
    equal_arrays = comparison.all()
    print(equal_arrays)


def test_pickle():
    rsc = RSCodec(10)
    shape = (10, 10, 10)
    input_array = np.random.randint(1000, size=shape)
    title = "util_msg_1"

    b = pickle.dumps(input_array)

    coded = title.encode() + b"\tab" + b

    print(coded)

    decoded = coded.split(b"\tab")

    print(decoded[0].decode("utf-8"))
    print(pickle.loads(decoded[1]))




if __name__ == '__main__':
    # test_serialize()

    test_pickle()
    # serialized = serialize(title="ACK", message="util_msg_1")
    # deserialized = deserialize(serialized)
    #
    # print(deserialized[1])
