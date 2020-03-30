import os
import numpy as np
import argparse
import sys

# Package
import agent
import dpop_parser
import network
import optimization
import utility
import pseudotree

Relatives = utility.Relatives

# def tree_opt(pstree, agents):
def tree_opt(agents):

    # no siblings
    pstree = {2: Relatives(parent='Nothing', pseudoparents=[], children=[0], pseudochildren=[3, 4]),
              0: Relatives(parent=2, pseudoparents=[], children=[1], pseudochildren=[3, 4]),
              1: Relatives(parent=0, pseudoparents=[], children=[3], pseudochildren=[]),
              3: Relatives(parent=1, pseudoparents=[0, 2], children=[4], pseudochildren=[]),
              4: Relatives(parent=3, pseudoparents=[0, 2], children=[], pseudochildren=[])}

    # with siblings
    pstree = {2: Relatives(parent='Nothing', pseudoparents=[], children=[0], pseudochildren=[1, 3, 4]),
              0: Relatives(parent=2, pseudoparents=[], children=[3], pseudochildren=[4]),
              3: Relatives(parent=0, pseudoparents=[2], children=[1, 4], pseudochildren=[]),
              1: Relatives(parent=3, pseudoparents=[2], children=[], pseudochildren=[]),
              4: Relatives(parent=3, pseudoparents=[0, 2], children=[], pseudochildren=[])}

    map_id_agent = {}
    for k in pstree.keys():
        for agent in agents:
            if agent.id == k:
                map_id_agent[k] = agent


    tree= {}
    for id in pstree.keys():
        if pstree[id].parent not in tree.keys():
            tree[pstree[id].parent] = [id]
        else:
            tree[pstree[id].parent] += [id]

    depths = pseudotree.assign_depths(tree)

    ants = {k: tuple(v.pseudoparents)+( v.parent, k) for k, v in pstree.items()}
    new_ants = {k: v[:-1] for k, v in ants.items()}
    ants={}

    for k, v in new_ants.items():
        if 'Nothing' not in v:
            ants[k] = v



    # sibling: the dictionary if the node has sibling of same parent
    silings={}
    for i in pstree.keys():
        for j in pstree.keys():
            if i != j:
                if pstree[i].parent == pstree[j].parent:
                    silings[i] = j
                    silings[j] = i

    # print(map_id_agent)
    print(ants)
    print(depths)

    optimal_sizes = [ optimization.optimize_size(map_id_agent[id],
        np.random.random(size=tuple(len(map_id_agent[x].domain) for x in ants[id])),
                       len(map_id_agent[ants[id][-1]].domain) if len(ants[id])>1 else 1 )
                     for id in ants.keys()]

    print(optimal_sizes)

    print("4", optimization.transmission_time(map_id_agent[4], (10,10,10), 340))
    print("4", optimization.computation_time(map_id_agent[4], 340))

    print("1", optimization.transmission_time(map_id_agent[1], (10, 10), 60))
    print("1", optimization.computation_time(map_id_agent[1], 60))

    print("1", optimization.transmission_time(map_id_agent[1], (10, 10), 30))
    print("1", optimization.computation_time(map_id_agent[1], 30))

    print("1", optimization.transmission_time(map_id_agent[1], (10, 10), 40))
    print("1", optimization.computation_time(map_id_agent[1], 40))



    if len(set(depths.values())) == len(pstree)+1: # all tree node has one parent
        # The optimization should be done in the linear method

        return
    else:

        return


def main(f, mode, computation, network):
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
        agents = [agent.Agent(i, d, agent_relations[i], "sim_jbs.tmp", computation, network) for i in agent_ids]
    elif mode == "list":
        agents = [agent.ListAgent(i, d, agent_relations[i], "sim_jbs.tmp", computation, network) for i in agent_ids]
    elif mode == "split":
        agents = [agent.SplitAgent(i, d, agent_relations[i], "sim_jbs.tmp", computation, network) for i in agent_ids]
    elif mode == "pipeline":
        agents = [agent.PipelineAgent(i, d, agent_relations[i], "sim_jbs.tmp", computation, network) for i in agent_ids]
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
                    a.tree_start()


    # Start root agent
    root_agent = agents[root_id]
    if pid == os.getpid():
        root_agent.tree_start()
        for _ in children:
            os.wait()

    return agents


def get_relatives(num_agents, constrains) -> dict:
    return {i: [[j for j in x if j != i][0] for x in constrains if i in x] for i in range(num_agents)}


if __name__ == '__main__':

    # default situations
    mode = "list"
    computation=1
    network=100
    datadir = "/Users/gx/Documents/Research_3/python_generator/data"
    num=5
    dom=10
    repo=7
    name=f"random_a{num}_d{dom}_r{repo}"
    input = f"{datadir}/{name}.xml"

    print("fuck")

    agents = main(f=input, mode=mode, computation=computation, network=network)

    tree_opt(agents)



class ModeError(Exception):
    "error type if a wrong mode is used"
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


