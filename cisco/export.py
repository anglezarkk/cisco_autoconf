import cisco.parser
import json
import ipaddress


class Export:
    def __init__(self, router_name, path="./config/topology.json", mode="full"):
        self.path = path
        self.mode = "full"  # could be "diff" for delta exports
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

            if 'mpls' in interface:
                config.append('mpls ' + interface['mpls'])

            # config.append('exit')

        return config

    def bgp(self):
        config = []

        if 'bgp' in self.topology:
            config.append('router bgp ' + self.topology['bgp']['asn'])
            if 'config' in self.topology['bgp']:
                for key, value in self.topology['bgp']['config'].items():
                    if value is True:
                        config.append('bgp ' + key)

            if 'neighbors' in self.topology['bgp']:
                for neighbor, neighbor_value in self.topology['bgp']['neighbors'].items():
                    for neighbor_element_key, neighbor_element_value in neighbor_value.items():
                        config.append(
                            'neighbor ' + neighbor + ' ' + neighbor_element_key + ' ' + neighbor_element_value)

            if 'afis' in self.topology['bgp']:
                for afi, afi_config in self.topology['bgp']['afis'].items():
                    config.append('address-family ' + afi.split('_', 1)[0])

                    if 'config' in afi_config:
                        for config_key, config_value in afi_config['config'].items():
                            config.append(config_key + ' ' + config_value)

                    if 'neighbors' in afi_config:
                        for neighbor_key, neighbor_value in afi_config['neighbors'].items():
                            for neighbor_element_key, neighbor_element_value in neighbor_value.items():
                                if neighbor_element_value is True:
                                    config.append('neighbor ' + neighbor_key + ' ' + neighbor_element_key)
                                else:
                                    config.append('neighbor ' + neighbor_key + ' ' +
                                                  neighbor_element_key + ' ' + neighbor_element_value)
                    config.append('exit-address-family')

            if 'vrfs' in self.topology['bgp']:
                for vrf, vrf_value in self.topology['bgp']['vrfs'].items():
                    config.append('address-family ' + vrf_value['afi'] + ' vrf ' + vrf)

                    if 'config' in vrf_value:
                        for config_key, config_value in vrf_value['config'].items():
                            config.append(config_key + ' ' + config_value)

                    if 'neighbors' in vrf_value:
                        for neighbor, neighbor_value in vrf_value['neighbors'].items():
                            if 'remote-as' in neighbor_value:
                                config.append('neighbor ' + neighbor + ' remote-as ' + neighbor_value['remote-as'])
                            for neighbor_element_key, neighbor_element_value in neighbor_value.items():
                                if neighbor_element_key != 'remote-as':
                                    if neighbor_element_value is True:
                                        config.append('neighbor ' + neighbor + ' ' + neighbor_element_key)
                                    else:
                                        config.append('neighbor ' + neighbor + ' ' + neighbor_element_key +
                                                      ' ' + neighbor_element_value)
                    config.append('exit-address-family')

        return config

    def ospf(self):
        config = []

        if 'ospf' in self.topology:
            config.append('router ospf ' + self.topology['ospf']['process_id'])
            for mpls_key, mpls_value in self.topology['ospf']['mpls'].items():
                config.append('mpls ' + mpls_key + ' ' + mpls_value)
            for network, network_val in self.topology['ospf']['networks'].items():
                config.append('network ' + network + ' ' + network_val['mask'] + ' area ' + network_val['area'])

        return config

    def mpls(self):
        config = []

        if 'mpls' in self.topology:
            for mpls_key, mpls_value in self.topology['mpls'].items():
                if mpls_key == 'router-id':
                    config.append('mpls ldp ' + mpls_key.replace('_', ' ') + ' ' + mpls_value + ' force')
                else:
                    config.append('mpls ' + mpls_key.replace('_', ' ') + ' ' + mpls_value)

        return config

    def vrfs(self):
        config = []

        if 'vrfs' in self.topology:
            for vrf_key, vrf_value in self.topology['vrfs'].items():
                config.append('ip vrf ' + vrf_key)
                for vrf_item_key, vrf_item_value in vrf_value.items():
                    config.append(vrf_item_key.replace('_', ' ') + ' ' + vrf_item_value)

        return config

    def generate_config(self):
        config_lines = [self.vrfs(), self.interfaces(), self.ospf(), self.bgp(), self.mpls()]

        with open("./config/exported_" + self.router_name + ".cfg", "w", encoding="utf-8") as fp:
            with open("./config/default.cfg", "r", encoding="utf-8") as fp_default:
                fp.write(fp_default.read())

            fp.write('hostname ' + self.router_name + '\n')
            for config_element in config_lines:
                for config_line in config_element:
                    fp.write(config_line + '\n')

            fp.write('end\n')
