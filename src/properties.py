import argparse
import json
import yaml
import yaml as yaml


def store_properties(properties: dict, file: str = "../properties.yaml"):
    with open(file, "w") as f:
        yaml.dump(properties, f)


def load_properties(file: str = "../properties.yaml"):
    properties = {}
    with open(file, "r") as f:
        docs = yaml.load_all(f, Loader=yaml.FullLoader)
        for doc in docs:
            for k, v in doc.items():
                properties[k] = v
    return properties


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
    args = parser.parse_args()

    properties = {}


    # "UDP", "TCP", "UDP_FEC"
    properties['network_protocol'] = args.network_protocol
    properties["agent_mode"] = args.mode
    properties["slow_processing"] = eval(args.computation)
    properties["comp_speed"] = args.comp_speed
    properties["network_customization"] = eval(args.network)
    properties["net_speed"] = args.net_speed

    store_properties(properties, "properties.yaml")
