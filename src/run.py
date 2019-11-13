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

# Package
import agent
import dpop_parser
import network
import optimization


def main(f, mode):
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
    for i in agent_ids:
        i_relation = {tu: relations[tu] for tu in relations.keys() if i in tu}
        keys = i_relation.keys()
        for tu in keys:
            if i != tu[0]:
                r_value = {(v_tu[1], v_tu[0]): i_relation[tu][v_tu] for v_tu in i_relation[tu].keys()}
                del i_relation[tu]
                i_relation[(tu[1], tu[0])] = r_value
        agent_relations[i] = i_relation

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
                    print('agent' + str(a.id) + ': ' + str(a.value))

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="# input file", type=str)
    parser.add_argument("--network", help="# if network customization is turned on", type=str, default="False")
    parser.add_argument("--mode", help="# which mode this algorithm is on {default, list, split, pipeline} ",
                        type=str, default="default")
    parser.add_argument("--comp_speed", help="# a parameter to adjust the computation speed ", type=float, default=10)
    parser.add_argument("--net_speed", help="# a parameter to adjust the network speed ", type=float, default=10)
    parser.add_argument("--pipeline", help="# a parameter wether pipeline is on ", type=str, default="False")
    # parser.add_argument("--output", help="# output file", type=str)
    args = parser.parse_args()

    network.network_customization = eval(args.network)
    network.net_speed = args.net_speed
    optimization.split_processing = False if args.mode in ["default", "list"] else True
    optimization.computation_speed = args.comp_speed

    main(f=args.input, mode=args.mode)


class ModeError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
