import sys
import numpy as np

with open(sys.argv[1]) as f:
    lines = f.readlines()

# print "#Messages sent:", sum([1 for x in lines if x.find('Message sent') != -1])
# print "#Messages received:", sum([1 for x in lines if x.find('Msg received') != -1])
# print "Size Messages received:", np.mean([int(x[x.find("is") + 3:x.find("bytes") - 1]) \
#                                           for x in lines if x.find('Msg received') != -1])
#
# print "Time spent:", int(lines[-1].strip())-int(lines[0].strip()), "s"

print(int(lines[-1].strip()) - int(lines[0].strip()))
