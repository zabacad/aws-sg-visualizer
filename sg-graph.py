#! /usr/bin/env python3

from boto3.session import Session
import colorsys
from graphviz import Digraph
import math

import sys


def main():
    x_spacing = 128
    y_spacing = -64

    session = Session()
    ec2 = session.client('ec2')

    security_groups = ec2.describe_security_groups()['SecurityGroups']
    cidrs = []

    managed   = Digraph('cluster_managed')
    unmanaged = Digraph('cluster_unmanaged')
    external  = Digraph('cluster_external')

    i, x, y = 0, 0, 0
    for sg in security_groups:
        x %= 32

        # Accumulate security groups
        sg_id = sg['GroupId']

        tags = {}
        for tag_blob in sg.get('Tags', {}):
            tags[tag_blob['Key']] = tag_blob['Value']

        sg_name   = tags.get('Name', '-')
        sg_desc   = sg.get('Description', '-')
        sg_puppet = True if tags.get('created_by', '').lower() == 'puppet' else False

        subgraph  = unmanaged
        color     = color_from_number(i)
        fontcolor = color
        if sg_puppet:
            subgraph  = managed
            fontcolor = 'black'

        sg_label = "{}\\n{}\\n{}".format(sg_name, sg_id, sg_desc)

        # Create security group nodes
        subgraph.node(
            sg_id,
            label=sg_label,
            shape='box',
            color=color,
            fontcolor=fontcolor,
            pos="{},{}".format(x*x_spacing, y*y_spacing)
        )

        i += 1
        x += 1
        y += 1

        # Accumulate rules (edges)
        rules_in = {}
        for rule_in in sg['IpPermissions']:
            protocol   = rule_in['IpProtocol'].upper()
            port_range = ''
            if protocol in ['TCP', 'UDP']:
                port_low   = rule_in['FromPort']
                port_high  = rule_in['ToPort']
                port_range = str(port_low) if port_low == port_high else "{}-{}".format(port_low, port_high)

            for sg_peer in rule_in.get('UserIdGroupPairs', {}):
                peer = sg_peer['GroupId']
                rules_in.setdefault(peer, {}).setdefault(protocol, []).append(port_range)

            for ip_peer in rule_in.get('IpRanges', {}):
                peer = ip_peer['CidrIp']
                rules_in.setdefault(peer, {}).setdefault(protocol, []).append(port_range)

                # Also create CIDRs nodes as discovered
                if peer not in cidrs:
                    cidrs.append(peer)
                    external.node(
                        peer,
                        shape='octagon',
                        pos="{},{}".format(x*x_spacing, y*y_spacing)
                    )

                    i += 1
                    x += 1
                    y += 1

        # Create rules (edges)
        for peer, rules in rules_in.items():
            label_parts = []
            for protocol, port_ranges in rules.items():
                label_parts.append("{}: {}".format(protocol, ', '.join(port_ranges)))

            label = '\\n'.join(sorted(label_parts))

            unmanaged.edge(
                peer,
                sg_id,
                label=label,
                color=color,
                fontcolor=color,
            )

    graph = Digraph(
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
    graph.subgraph(managed)
    graph.subgraph(unmanaged)
    graph.subgraph(external)

    print(graph.source)


def color_from_number(number, num_options=16):
    red, green, blue = map(math.floor, [e * 255 for e in colorsys.hsv_to_rgb(number / num_options, 1, 0.6)])

    return "#{:0>2x}{:0>2x}{:0>2x}".format(red, green, blue)


if __name__ == '__main__':
    main()
