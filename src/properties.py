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
    properties = {}

    # "UDP", "TCP", "UDP_FEC"
    properties['network_protocol'] = "UDP_FEC"

    store_properties(properties)
