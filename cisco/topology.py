import cisco.dump
import ipaddress
import json
from ciscoconfparse import CiscoConfParse

class Topology:
    def __init__(self, routers):
        self.interfaces_connections = None
        self.routers = routers

    def find_interfaces_connections(self):
        data = {}
        for router1 in self.routers:
            data[router1] = []
            dump_obj1 = cisco.dump.Dump(router1, 0, 0)
            parser_1 = CiscoConfParse(dump_obj1.get_config_filename(), syntax="ios", factory=True)
            intf_1 = parser_1.find_objects("interface Gigabit")

            for router2 in self.routers:
                if router1 == router2:
                    print("[debug] same router, skip")
                else:
                    dump_obj2 = cisco.dump.Dump(router2, 0, 0)
                    parser_2 = CiscoConfParse(dump_obj2.get_config_filename(), syntax="ios", factory=True)
                    intf_2 = parser_2.find_objects("interface Gigabit")

                    for interface_1 in intf_1:
                        if interface_1.ipv4_addr != "":
                            net_1 = ipaddress.ip_network(interface_1.ipv4_addr + '/' + str(interface_1.ipv4_masklength), False)
                            for interface_2 in intf_2:
                                if interface_2.ipv4_addr != "":
                                    net_2 = ipaddress.ip_network(interface_2.ipv4_addr + '/' + str(interface_2.ipv4_masklength), False)
                                    if net_1 == net_2:
                                        src = interface_1.port_type + interface_1.interface_number
                                        dst = { "target_router":router2, "target_interface": interface_2.port_type + interface_2.interface_number}
                                        data[router1].append({src:dst})

        self.interfaces_connections = data
        return data

    def output_topology(self):
        with open("topology.json", "w", encoding="utf-8") as fp:
            json.dump(self.interfaces_connections, fp, ensure_ascii=False, indent=4)
