#! /usr/bin/env python3

from SecurityGroup import *
from Cidr import *

import argparse
import boto3.session
import colorsys
from graphviz import Digraph
import math
import sys


def main():
    parser = argparse.ArgumentParser('Generate a graph of AWS security groups.')

    parser.add_argument('-o', '--output',
        help='Output dot-format file. Default stdout.',
        type=argparse.FileType('w'),
        default=sys.stdout,
    )

    args = parser.parse_args()

    args.output.write(generate_graph(collect_security_groups()))


def generate_graph(security_groups_raw):
    x_spacing = 1
    y_spacing = -1

    i, x, y = 0, 0, 0

    vpcs_sgs = {}
    cidrs    = CidrSet()

    vpc_graphs = {}
    external   = Digraph('cluster_external')
    unused     = Digraph('cluster_unused')

    for sg in security_groups_raw:
        security_group = SecurityGroup(sg)
        vpcs_sgs.setdefault(security_group.vpc, SecurityGroupSet()).add_security_group(security_group)

    for vpc, sg_set in vpcs_sgs.items():
        for sg_id, sg in sg_set.security_groups.items():
            for ingress in sg.ingress:
                if ingress.peer_type in ('cidr', 'ip'):
                    cidrs.add_cidr(ingress.peer, sg)

                elif ingress.peer_type == 'sg':
                    if ingress.peer_loc in vpcs_sgs:
                        vpcs_sgs[ingress.peer_loc].security_groups[ingress.peer].add_reverse_rule('ingress_to', ingress)
                    #else:
                    #    print("Skipping peer '{}' in unknown VPC '{}' for security group '{}'.".format(ingress.peer, ingress.peer_loc, sg_id))
        
            for egress in sg.egress:
                if egress.peer_type in ('cidr', 'ip'):
                    cidrs.add_cidr(egress.peer, sg)

                elif egress.peer_type == 'sg':
                    vpcs_sgs[egress.peer_loc].security_groups[egress.peer].add_reverse_rule('egress_from', egress)

    for vpc_id, sgs in vpcs_sgs.items():
        vpc_subgraph = Digraph('cluster_' + str(vpc_id))
        vpc_graphs[vpc_id] = vpc_subgraph

        # Create security group nodes
        for sg_id, sg in sgs.security_groups.items():
            x %= 32
            subgraph = vpc_subgraph

            color     = color_from_number(i)
            fontcolor = color
            if not sg.peers():
                subgraph = unused

            #print("Adding node to subgraph {}: {}".format(subgraph.name, sg.id))
            subgraph.node(
                sg.id,
                label=sg.label,
                shape='box',
                color=color,
                fontcolor='white',
                style='filled',
                pos="{},{}!".format(x*x_spacing, y*y_spacing)
            )

            i += 1
            x += 1
            y += 1

            # Create rules (edges)
            for rule in sg.ingress:
                #print("Adding edge in subgraph {} between: {}, {}".format(subgraph.name, rule.peer, sg.id))
                subgraph.edge(
                    rule.peer,
                    sg.id,
                    label=rule.label,
                    color=color,
                    fontcolor=color,
                    pos="{},{}!".format(x*x_spacing, y*y_spacing)
                )

    # Create CIDR nodes
    for cidr, peers in cidrs.cidrs.items():
        x %= 32
        #print('Adding CIDR/IP node ' + cidr)
        external.node(cidr,
            label=cidr,
            shape='octagon',
            color='black',
            fontcolor='white',
            style='filled',
            pos="{},{}!".format(x*x_spacing, y*y_spacing)
        )

        i += 1
        x += 1
        y += 1

    main_graph = Digraph(
        graph_attr={
            'splines': 'ortho'
        },
        node_attr={
            'fontname': 'Sans',
            'fontsize': '8',
        },
        edge_attr={
            'fontname': 'Sans',
            'fontsize': '8',
        }
    )

    for vpc_id, graph in vpc_graphs.items():
        main_graph.subgraph(graph)

    main_graph.subgraph(external)
    #main_graph.subgraph(unused)

    return main_graph.source


def color_from_number(number, num_options=16):
    red, green, blue = map(math.floor, [e * 255 for e in colorsys.hsv_to_rgb(number / num_options, 1, 0.6)])

    return "#{:0>2x}{:0>2x}{:0>2x}".format(red, green, blue)


def collect_security_groups():
    session = boto3.session.Session()
    ec2 = session.client('ec2')

    sg_req = {
        'MaxResults': 100,
    }

    while True:
        sg_resp = ec2.describe_security_groups(**sg_req)
        for sg in sg_resp['SecurityGroups']:
            yield sg

        if 'NextToken' not in sg_resp: break

        sg_req['NextToken'] = sg_resp['NextToken']


if __name__ == '__main__':
    main()
