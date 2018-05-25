

class CidrSet:
    def __init__(self):
        self.cidrs = {}

    def add_cidr(self, cidr, sg):
        cleaned = cidr
        if cidr.endswith('/32'):
            cleaned = cidr[:-3]

        self.cidrs.setdefault(cleaned, []).append(sg)
