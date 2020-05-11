import logging

from reedsolo import RSCodec, ReedSolomonError

import numpy as np

import utility

logger = logging.getLogger("RSCoding")


# Supoorts Reed Soloomon codes

def example():
    rsc = RSCodec(10)

    # Encoding
    raw_list = rsc.encode([1, 2, 3, 4])
    print(raw_list)
    byte_array = rsc.encode(bytearray([1, 2, 3, 4]))
    print(byte_array)
    b_str = rsc.encode(b'hello world')
    print(b_str)
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
    shape = np.frombuffer(combined_decoded[1], "int64")
    # shape = np.frombuffer(combined_decoded[1].encode(), "int64")
    data = np.frombuffer(combined_decoded[2], datatype)



    if title == "ptinfo":
        return title, load_relatives(data)
    elif "domain_" in title:
        return title, list(data)
    elif "pre_util_msg_'" in title:
        return title, tuple(data)
    elif "value_msg_" in title:
        return title, load_dict(data)
    else:
        return title, data.reshape(shape)


def serialize(title: str, input_array, rsc: RSCodec = RSCodec(10)) -> bytearray:
    if isinstance(input_array, np.ndarray):
        shape = np.asarray(input_array.shape)
        b = input_array.tobytes()
    elif isinstance(input_array, list) or \
            (isinstance(input_array, tuple) and not isinstance(input_array, utility.Relatives)):
        shape = np.asarray(len(input_array))
        b = np.asarray(input_array).tobytes()
    elif isinstance(input_array, utility.Relatives):
        data = dump_relatives(input_array)
        shape = np.asarray(len(data))
        b = np.asarray(data).tobytes()
    elif isinstance(input_array, dict):
        data = dump_dict(input_array)
        shape = np.asarray(len(data))
        b = np.asarray(data).tobytes()
    else:
        logger.error(f"not supportd input: {title}  {input_array} {type(input_array)}")
        raise Exception(f"not supportd input {type(input_array)}")

    combined_str = title.encode() + b"\tab" + shape.tobytes() + b"\tab" + b

    return rsc.encode(combined_str)


def load_dict(l: list) -> dict:
    if len(l) % 2 == 0:
        d = {int(l[2 * i]): int(l[2 * i + 1]) for i in range(len(l) // 2)}
    else:
        logger.error(f"list input l is not with correct length: {len(l)}")
        raise Exception(f"list input l is not with correct length: {len(l)}")
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


def load_relatives(l) -> utility.Relatives:
    if not isinstance(l, list):
        l = list(l)
    index = l[:3]
    values = l[3:]

    r = utility.Relatives(int(values[0]),
                          [int(x) for x in values[1:index[1]]],
                          [int(x) for x in values[index[1]:index[2]]],
                          [int(x) for x in values[index[2]:]])
    return r


def dump_relatives(relatives: utility.Relatives) -> list:
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
    shape = [10, 10, 10]
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
    serialized = serialize(title="ssss", input_array=input_array)
    deserialized = deserialize(serialized)

    print(deserialized[0])
    print(input_array)
    # comparison = input_array == deserialized[1]
    comparison = input_array == deserialized[1]
    equal_arrays = comparison.all()
    print(equal_arrays)


if __name__ == '__main__':
    d = {}
    d["222"] = 2
    d["sss"] = 5

    print(dump_dict(d))
