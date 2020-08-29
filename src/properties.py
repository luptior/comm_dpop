"""
prop.py
a script that takes in command line input and set up a local yaml configuration file for dcop running

@author gan.xu
"""

import argparse
import json
import yaml
import yaml as yaml


def store_properties(prop: dict, file: str = "../properties.yaml"):
    with open(file, "w") as f:
        yaml.dump(prop, f)


def load_properties(file: str = "../properties.yaml"):
    prop = {}
    with open(file, "r") as f:
        docs = yaml.load_all(f, Loader=yaml.FullLoader)
        for doc in docs:
            for k, v in doc.items():
                prop[k] = v
    return prop


def add_argument(file: str, t):

    props = load_properties(file)

    props["start_time"] = t

    store_properties(props, file)



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--network_protocol", help="# which network protocol is on {TCP, UDP, UDP_FEC}",
                        type=str, default="TCP")
    parser.add_argument("--network", help="# if network customization is turned on", type=str, default="False")
    parser.add_argument("--mode", help="# which mode this algorithm is on {default, list, split, pipeline} ",
                        type=str, default="default")
    parser.add_argument("--computation", help="# whether to adjust the computation speed ", type=str, default="False")
    parser.add_argument("--comp_speed", help="# a parameter to adjust the computation speed ", type=float, default=1000)
    parser.add_argument("--net_speed", help="# a parameter to adjust the network speed ", type=float, default=1000)
    parser.add_argument("--log_file", help="# path to output log ", type=str)
    parser.add_argument("--ber", help="# bit error rate", type=float, default=0) # default to be always correct
    parser.add_argument("--drop", help="# packet drop rate", type=float, default=0)  # default to be always correct
    parser.add_argument("--rtt", help="# round trip time", type=float, default=0.01)  # default to be always correct
    args = parser.parse_args()

    properties = {'network_protocol': args.network_protocol,
                  "agent_mode": args.mode,
                  "slow_processing": eval(args.computation),
                  "comp_speed": args.comp_speed,
                  "network_customization": eval(args.network),
                  "net_speed": args.net_speed,
                  "log_file": args.log_file,
                  "ber": args.ber,
                  "drop": args.drop,
                  "rtt": args.rtt}

    store_properties(properties, "properties.yaml")
