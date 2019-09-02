"""The entry point of the program
Parse the input files
Setting up the agents
Start the running.


xml_parser can be change to other scripts to read different types of input.
"""


import os
import sys
import numpy as np
import argparse

# Package
import agent
import dpop_parser

network_customization = False

def get_relatives(num_agents, contatints):
    return {i: [[j for j in x if j != i][0] for x in contatints if i in x] for i in range(num_agents)}


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
    for i in agent_ids:
        i_relation = {tu:relations[tu] for tu in relations.keys() if i in tu}
        keys = i_relation.keys()
        for tu in keys:
            if i != tu[0]:
                r_value = {(v_tu[1], v_tu[0]):i_relation[tu][v_tu] for v_tu in i_relation[tu].keys()}
                del i_relation[tu]
                i_relation[(tu[1], tu[0])]=r_value
        agent_relations[i] = i_relation

    with open("sim_jbs.txt", "w") as f:
        f.write("id=42 root_id=" + str(root_id) + "\n\n")
        id = np.random.randint(1000)
        for u in agent_ids:
            f.write("id=" + str(u) + " ")
            f.write("IP=127.0.0.1" + " ")
            f.write("PORT=" + str(5000 + id + u) + " ")
            if u == root_id:
                f.write("is_root=True" + " ")
            f.write("\n\n")

    agents = [agent.Agent(i, d, agent_relations[i], "sim_jbs.txt")
              for i in agent_ids]

    # Running the agents
    pid = os.getpid()
    children = []

    for a in agents:
        if not a.is_root:
            if pid == os.getpid():
                childid = os.fork()
                children.append(childid)
                if childid == 0:
                    a.start()
                    print('agent' + str(a.id) + ': ' + str(a.value))

    # Start root agent
    root_agent = agents[root_id]
    if pid == os.getpid():
        root_agent.start()
        print('max_util: ' + str(root_agent.max_util))
        print('agent' + str(root_agent.id) + ': ' + str(root_agent.value))
        for i in children:
            os.wait()

    ### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - ###


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="# input file", type=str)
    parser.add_argument("--network", help="# if network customization is turned on", type=str, default="False")
    # parser.add_argument("--output", help="# output file", type=str)
    args = parser.parse_args()

    network_customization = eval(args.network)

    main(f=args.input)
