"""The entry point of the program
Parse the input files
Setting up the agents
Start the running.

xml_parser can be change to other scripts to read different types of input.
"""

import os
import numpy as np
import argparse
import sys
import logging

# Package
import agent
import dpop_parser
import network
import optimization

import properties as prop

def main(f):
    if f.split(".")[-1] == "xml":
        agents, domains, variables, relations, constraints = dpop_parser.xml_parse(f)
    else:
        agents, domains, variables, relations, constraints = dpop_parser.parse(f)

    agent_ids = list(range(len(agents)))
    root_id = int(len(agent_ids) / 2)
    d = list(range(domains['d']['domain_range'][0], domains['d']['domain_range'][1] + 1))

    r = [tuple([int(i) for i in x.split("_")[1:]]) for x in relations.keys()]

    relations = {x: relations["".join(["r_", str(x[0]), "_", str(x[1])])]["relations"] for x in r}

    # dict keys are agent id and values are (agent_id, neighbor_id):{(val1, val2):util}
    agent_relations = {}

    for agent_id in agent_ids:
        # id_pair: (agent_id, neighbor_id), agent_relation: (this_agent_id, neighbor_id):{(val1, val2):util}
        # select entrys with this agent_id in it
        agent_relation = {id_pair: relations[id_pair] for id_pair in relations.keys() if agent_id in id_pair}
        agent_relation2 = {} # updated with this agent_id always at (*, other )
        id_pairs = agent_relation.keys()
        for id_pair in id_pairs:
            if agent_id != id_pair[0]:
                r_value = {(v_tu[1], v_tu[0]): agent_relation[id_pair][v_tu] for v_tu in agent_relation[id_pair].keys()}
                agent_relation2[(id_pair[1], id_pair[0])] = r_value
            else:
                agent_relation2[id_pair] = agent_relation[id_pair]
        agent_relations[agent_id] = agent_relation2

    with open("sim_jbs.tmp", "w") as f:
        f.write("id=42 root_id=" + str(root_id) + "\n\n")
        id = np.random.randint(1000)
        for u in agent_ids:
            f.write("id=" + str(u) + " ")
            f.write("IP=127.0.0.1" + " ")
            f.write("PORT=" + str(5000 + id + u) + " ")
            if u == root_id:
                f.write("is_root=True" + " ")
            f.write("\n\n")

    properties = prop.load_properties("properties.yaml")
    mode = properties["agent_mode"]


    if mode == "default":
        agents = [agent.Agent(i, d, agent_relations[i], "sim_jbs.tmp") for i in agent_ids]
    elif mode == "list":
        agents = [agent.ListAgent(i, d, agent_relations[i], "sim_jbs.tmp") for i in agent_ids]
    elif mode == "split":
        agents = [agent.SplitAgent(i, d, agent_relations[i], "sim_jbs.tmp") for i in agent_ids]
    elif mode == "pipeline":
        agents = [agent.PipelineAgent(i, d, agent_relations[i], "sim_jbs.tmp") for i in agent_ids]
    else:
        raise ModeError(mode)

    # Running the agents
    pid = os.getpid()
    children = []

    for a in agents:
        if not a.is_root:
            if pid == os.getpid():
                child_id = os.fork()
                children.append(child_id)
                if child_id == 0:
                    a.start()
                    logger.debug('agent' + str(a.id) + ': ' + str(a.value))

    # Start root agent
    root_agent = agents[root_id]
    if pid == os.getpid():
        root_agent.start()
        print('max_util: ' + str(root_agent.max_util))
        print('agent' + str(root_agent.id) + ': ' + str(root_agent.value))
        for _ in children:
            os.wait()


def get_relatives(num_agents, constrains) -> dict:
    return {i: [[j for j in x if j != i][0] for x in constrains if i in x] for i in range(num_agents)}


if __name__ == '__main__':

    logger = logging.getLogger("MAIN")
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler("log.txt")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="# input file", type=str)

    # parser.add_argument("--output", help="# output file", type=str)
    args = parser.parse_args()

    main(f=args.input)


class ModeError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
