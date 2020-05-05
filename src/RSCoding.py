from reedsolo import RSCodec, ReedSolomonError

import numpy as np


# Supoorts Reed Soloomon codes

def example():
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


def long_coding():
    table = np.random.randint(10, size=[5, 5, 5, 5])
    table_rs = rsc.encode(table.tobytes())
    print(len(rsc.decode(table_rs)))


# for the combined messages
def deserialize(input: bytearray, rsc: RSCodec = RSCodec(10), datatype="int64"):
    combined = rsc.decode(input)[0]
    # symbol
    combined_decoded = combined.split(b";")
    # [title, shape, actual data]
    title = combined_decoded[0].decode()
    shape = np.frombuffer(combined_decoded[1], "int64")
    # shape = np.frombuffer(combined_decoded[1].encode(), "int64")
    data = np.frombuffer(combined_decoded[2], datatype)

    return title, data.reshape(shape)


def serialize(title: str, input_array, rsc: RSCodec = RSCodec(10)) -> bytearray:
    if isinstance(input_array, np.ndarray):
        shape = np.asarray(input_array.shape)
        b = input_array.tobytes()
    elif isinstance(input_array, list):
        shape = np.asarray(len(input_array))
        b = np.asarray(input_array).tobytes()
    combined_str = title.encode() + b";" + shape.tobytes() + b";" + b

    return rsc.encode(combined_str)


if __name__ == '__main__':
    rsc = RSCodec(10)  # 10 ecc symbols\
    # rsc2 = RSCodec(10) # another
    shape = [2, 3, 4]
    #
    #
    input_array = np.random.randint(10, size=shape)
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
    serialized = serialize(title="ssss", input_array=shape)
    deserialized = deserialize(serialized)

    print(deserialized[0])
    # comparison = input_array == deserialized[1]
    comparison = np.asarray(shape) == deserialized[1]
    equal_arrays = comparison.all()
    print(equal_arrays)
