import cisco.parser
import json
import ipaddress


class Export:
    def __init__(self, router_name, path = "./config/topology.json", mode = "full"):
        self.path = path
        self.mode = "full" # could be "diff" for delta exports
        self.router_name = router_name
        self.topology = self.read_topology()

    def read_topology(self):
        with open(self.path, "r") as fp:
            topology = json.load(fp)

        return topology[self.router_name]

    def interfaces(self):
        config = []
        for interface_name in self.topology['interfaces']:
            interface = self.topology['interfaces'][interface_name]
            ip_net = ipaddress.IPv4Interface(interface['ipv4'])

            config.append('interface ' + interface_name)
            config.append('ip address ' + str(ip_net.ip) + ' ' + str(ip_net.netmask))

            if not interface['shutdown']:
                config.append('no shutdown')

            config.append('exit')

    def ospf(self):
        print('a')

    def bgp(self):
        print('a')

    def mpls(self):
        print('a')



