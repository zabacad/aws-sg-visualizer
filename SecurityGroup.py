import re


class SecurityGroupSet:
    def __init__(self):
        self.security_groups = {}

    def add_security_group(self, security_group):
        self.security_groups[security_group.id] = security_group


class SecurityGroup:
    def __init__(self, sg_dict):
        self.id     = sg_dict['GroupId']
        self.sgname = sg_dict.get('GroupName')
        self.desc   = sg_dict.get('Description')
        self.owner  = sg_dict.get('OwnerId')
        self.vpc    = sg_dict.get('VpcId')

        # Rules part of this group.
        self.ingress = []
        self.egress  = []

        # Rules in other groups that reference this one.
        # Populated by calls to `add_reverse_rule`.
        self.ingress_to  = []
        self.egress_from = []

        for rule in sg_dict.get('IpPermissions', []):
            for rule_type in [
                'IpRanges',
                'Ipv6Ranges',
                'PrefixListIds',
                'UserIdGroupPairs',
            ]:
                for rule_permission in rule.get(rule_type, []):
                    self.ingress.append(SecurityGroupRule(
                        self,
                        'ingress',
                        rule['IpProtocol'],
                        rule.get('FromPort', -1),
                        rule.get('ToPort', -1),
                        rule_type,
                        rule_permission,
                    ))

        # TODO: egress

        self.tags = {}
        for tag_blob in sg_dict.get('Tags', {}):
            if tag_blob['Key'] == 'Name':
                self.name = tag_blob['Value']
            else:
                self.tags[tag_blob['Key']] = tag_blob['Value']

        if not hasattr(self, 'name'):
            self.name = self.sgname
            self.no_name_tag = True

        self.label = "{} ({})".format(self.name, self.id)

    def add_reverse_rule(self, direction, rule):
        if direction == 'ingress_to':
            self.ingress_to.append(rule)
        elif direction == 'egress_from':
            self.egress_from.append(rule)
        else:
            raise ValueError('Unknown reverse rule direction: ' + direction)

    def peers(self):
        peers = []
        peers += [ingress.peer for ingress in self.ingress]
        peers += [egress.peer for egress in self.egress]
        peers += [ingress_to.peer for ingress_to in self.ingress_to]
        peers += [egress_from.peer for egress_from in self.egress_from]

        return peers


class SecurityGroupRule:
    def __init__(self, parent_group, direction, proto, port_low, port_high, peer_type, peer_dict):
        self.direction = direction

        self.proto = str(proto).upper()
        if self.proto == '-1':
            self.proto = 'all'

        self.port_low  = port_low
        self.port_high = port_high

        self.port_label = str(self.port_low) + '..' + str(self.port_high)
        if self.port_low == -1:
            self.port_label = 'all'
        elif self.port_low == self.port_high:
            self.port_label = str(self.port_low)

        self.label = self.proto + ': ' + self.port_label

        self.peer      = re.sub('[^a-zA-Z0-9_-]', '', repr(peer_dict))
        self.peer_type = peer_type

        if peer_type == 'IpRanges':
            self.peer_type = 'cidr'
            self.peer_loc  = 'internet'  # TODO: See if it's a private IP.
            self.peer      = peer_dict['CidrIp']

            if self.peer.endswith('/32'):
                self.peer_type = 'ip'
                self.peer      = peer_dict['CidrIp'][:-3]
        elif peer_type == 'Ipv6Ranges':
            # TODO
            pass
        elif peer_type == 'PrefixListIds':
            # TODO
            pass
        elif peer_type == 'UserIdGroupPairs':
            self.peer_type  = 'sg'
            self.peer_loc   = peer_dict.get('VpcId', parent_group.vpc)
            self.peer       = peer_dict['GroupId']
