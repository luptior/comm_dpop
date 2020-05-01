from reedsolo import RSCodec, ReedSolomonError

import numpy as np

1,502.07

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
    table = np.random.randint(10, size=[5,5,5,5])
    table_rs = rsc.encode(table.tobytes())
    print(len(rsc.decode(table_rs)))


def deserilze(rsc: RSCodec, input: bytearray, shape, type = "int64")-> np.ndarray:
    # symbol
    return np.frombuffer(rsc.decode(input)[0], dtype=type).reshape(shape)

def serilze(rsc: RSCodec, input_array: np.ndarray)->bytearray:

    return rsc.encode(input_array.tobytes())


if __name__ == '__main__':
    rsc = RSCodec(10)  # 10 ecc symbols\
    shape = [2,3,3,4]
    input_array = np.random.random(size=shape)

    comparison =  input_array == deserilze(rsc, serilze(rsc, input_array), shape)
    equal_arrays = comparison.all()

    print(equal_arrays)