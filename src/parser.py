"""
A script parsing simulated files for DCOP running

A generator https://github.com/luptior/dcop_generator

@auther gan.xu
"""

import re
import sys
import xml.etree.ElementTree as ET


def parse(file: str):
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
        scope = l[loci_quotas[4] + 1: loci_quotas[5]].split(" ")
        name, line_dict = line_parser(l)
        line_dict["scope"] = scope
        return name, line_dict

    agents = []
    variables = {}
    domains = {}
    relations = {}
    constraints = {}

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


def xml_parse(f: str):
    tree = ET.parse(f)
    root = tree.getroot()

    agents = []
    variables = {}
    domains = {}
    relations = {}
    constraints = {}

    data = {x.tag: x for x in root}

    # processing agents
    for agent in data['agents']:
        agents.append(agent.attrib['name'])

    # processing variables
    for v in data['variables']:
        variables[v.attrib["name"]] = {"agent": v.attrib["agent"]}
        variables[v.attrib["name"]]["domain"] = v.attrib["domain"]

    # processing domain
    for d in data['domains']:
        domains[d.attrib["name"]] = {'nbValues': d.attrib['nbValues']}
        domains[d.attrib["name"]]['domain_range'] = [int(x) for x in d.text.split("..")]

    # processing relations
    for r in data['relations']:
        relations[r.attrib['name']] = r.attrib
        relations[r.attrib['name']]['relations'] = \
            {tuple([int(x) for x in x.strip().split(":")[-1].split()]): int(x.strip().split(":")[0]) \
             for x in r.text.strip("|").split("|")}

    # processing constrains
    for c in data['constraints']:
        constraints[c.attrib['name']] = c.attrib
        constraints[c.attrib['name']]['scope'] = constraints[c.attrib['name']]['scope'].split()

    return agents, domains, variables, relations, constraints
