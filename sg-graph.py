#! /usr/bin/env python3

from boto3.session import Session
from graphviz import Digraph


def main():
    session = Session()
    ec2 = session.client('ec2')

    security_groups = ec2.describe_security_groups()['SecurityGroups']

    managed   = Digraph('cluster_managed')
    unmanaged = Digraph('cluster_unmanaged')

    for sg in security_groups:
        sg_id = sg['GroupId']

        tags = {}
        for tag_blob in sg.get('Tags', {}):
            tags[tag_blob['Key']] = tag_blob['Value']

        sg_name = tags.get('Name', '-')
        sg_desc = sg.get('Description', '-')
        sg_puppet = True if tags.get('created_by', '').lower() == 'puppet' else False

        subgraph = unmanaged
        color    = 'black'
        if sg_puppet:
            subgraph = managed
            color    = 'blue'

        sg_label = "{}\\n{}\\n{}".format(sg_name, sg_id, sg_desc)

        subgraph.node(sg_id, shape='box', label=sg_label, fontname='Sans', color=color)

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

        for peer, rules in rules_in.items():
            label_parts = []
            for protocol, port_ranges in rules.items():
                label_parts.append("{}: {}".format(protocol, ', '.join(port_ranges)))

            label = '\\n'.join(sorted(label_parts))
            unmanaged.edge(peer, sg_id, label=label, fontname='Sans')

    graph = Digraph()
    graph.subgraph(managed)
    graph.subgraph(unmanaged)

    print(graph.source)


if __name__ == '__main__':
    main()
