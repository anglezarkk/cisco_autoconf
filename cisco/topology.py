import cisco.dump
import cisco.parser
import ipaddress
import json
from ciscoconfparse import CiscoConfParse


# Topology class
# An bunch of functions to understand the topology of selected routers
class Topology:
    def __init__(self, routers):
        self.routers = routers

    # get relationships between interfaces of selected routers + addresses
    def find_interfaces_connections(self):
        data = {}
        for router1_obj in self.routers:
            router1 = router1_obj["name"]
            data[router1] = {}
            dump_obj1 = cisco.dump.Dump(router1, 0, 0)
            parser_1 = CiscoConfParse(dump_obj1.get_config_filename(), syntax="ios", factory=True)
            intf_1 = parser_1.find_objects("interface")

            for router2_obj in self.routers:
                router2 = router2_obj["name"]
                if router1 == router2:
                    print("[debug] same router, skip")
                else:
                    dump_obj2 = cisco.dump.Dump(router2, 0, 0)
                    parser_2 = CiscoConfParse(dump_obj2.get_config_filename(), syntax="ios", factory=True)
                    intf_2 = parser_2.find_objects("interface")

                    for interface_1 in intf_1:
                        src = interface_1.port_type + interface_1.interface_number
                        dst = None
                        if interface_1.ipv4_addr != "":
                            net_1 = ipaddress.ip_network(interface_1.ipv4_addr + '/' + str(interface_1.ipv4_masklength),
                                                         False)
                            for interface_2 in intf_2:
                                if interface_2.ipv4_addr != "":
                                    net_2 = ipaddress.ip_network(
                                        interface_2.ipv4_addr + '/' + str(interface_2.ipv4_masklength), False)
                                    if net_1 == net_2:
                                        dst = {"target_router": router2,
                                               "target_interface": interface_2.port_type + interface_2.interface_number,
                                               "ipv4": interface_1.ipv4_addr + "/" + str(interface_1.ipv4_masklength),
                                               "shutdown": interface_1.is_shutdown,
                                               }
                                        data[router1].update({src: dst})
                            # handle interfaces with ip, not connected to other routers
                            if dst is None:
                                intf_info = {"ipv4": interface_1.ipv4_addr + "/" + str(interface_1.ipv4_masklength),
                                             "shutdown": interface_1.is_shutdown}
                                data[router1].update({src: intf_info})

                        else:
                            src = interface_1.port_type + interface_1.interface_number
                            info = {"shutdown": interface_1.is_shutdown}
                            data[router1].update({src: info})

        return data

    # Get BGP information for selected routers
    def bgp_analysis(self):
        data = {}
        for router_obj in self.routers:
            router = router_obj['name']
            routerdump = cisco.dump.Dump(router, 0, 0)
            parser = CiscoConfParse(routerdump.get_config_filename(), syntax="ios", factory=True)
            objects = parser.find_objects("router bgp")
            if objects:
                for current_object in objects:
                    data[router] = {}
                    bgp_json = cisco.parser.bgp(current_object.ioscfg)
                    data[router].update({'bgp': bgp_json[0]['bgp']})

        return data

    # merge all infos into one file, JSON format
    def output_topology(self):
        interfaces_connections = self.find_interfaces_connections()
        bgp_informations = self.bgp_analysis()

        data = {}
        for router_obj in self.routers:
            router = router_obj["name"]
            data[router] = {}
            if router in bgp_informations:
                data[router].update(bgp_informations[router])
            if router in interfaces_connections:
                data[router]['interfaces'] = interfaces_connections.get(router)

        with open("./config/topology.json", "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=4)
