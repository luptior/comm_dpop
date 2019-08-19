"""
script parsing simulated XML file for DCOP

"""


import re
import sys

agents = []
domains = {}
variables = {}
relations = {}
constraints = {}


def parse(file="/Users/luptior/Desktop/Rotation_3/dcop_generator/build/agents/rep_0_agents.xml"):
    with open(file) as input:
        for line in input.readlines():
            if line.find("agent name") != -1:
                # get the names of agents
                start = line.find("=")
                end = line.find("/")
                agents.append(line[start + 1: end].strip("\""))
            elif line.find("domain name") != -1:
                # get the name of domains and their values
                name, props = line_parser_domain(line)
                domains[name] = props
            elif line.find("variable name") != -1:
                # get the varibale names and properties
                name, props = line_parser(line)
                variables[name] = props
            elif line.find("relation name") != -1:
                name, props = line_parser_relation(line)
                relations[name] = props
            elif line.find("constraint name") != -1:
                name, props = line_parser_constraint(line)
                constraints[name] = props

    return agents, domains, variables, relations, constraints


def line_parser(l):
    # parse a line and return its name and rest info dict
    line_dict = {x.split("=")[0]: x.split("=")[1].strip().strip(">").strip("/").strip("\"")
                 for x in l.split(" ") if "=" in x}
    name = line_dict.pop("name")
    return name, line_dict


def line_parser_domain(l):
    # parse domain type line
    name, line_dict = line_parser(l[:l.find(">")])
    domain_range = l[l.find(">") + 1: l.find("</")].split("..")
    line_dict["domain_range"] = [int(x) for x in domain_range]
    return name, line_dict


def line_parser_relation(l):
    # parse relation type line
    name, line_dict = line_parser(l[:l.find(">")])
    relation = {tuple([int(y) for y in x.split(":")[1].split(" ")[:2]]): int(x.split(":")[0])
                 for x in l[l.find(">") + 1: l.find("</")].split("|")}
    line_dict["relations"] = relation
    return name, line_dict


def line_parser_constraint(l):
    loci_quotas = [m.start() for m in re.finditer("\"", l)]
    scope = l[loci_quotas[4]+1: loci_quotas[5]].split(" ")
    name, line_dict = line_parser(l)
    line_dict["scope"] = scope
    return name, line_dict


if __name__ == '__main__':
    print(parse(sys.argv[1]))
