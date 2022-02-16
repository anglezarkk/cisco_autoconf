import json

from netaddr import IPNetwork


class Enrich:
    simplified_json = {}
    enriched_json = {}
    internal_ip = ""
    internal_subnets = ""
    border_ip = ""
    border_subnets = ""
    customer_ip = ""
    customer_subnets = ""
    mpls_bgp_vpn = False
    bgp_auto_peering = False
    as_id = 100

    def __init__(self, file_path):
        with open(file_path) as json_file:
            self.simplified_json = json.load(json_file)

            self.internal_ip = IPNetwork(self.simplified_json["internal_auto_allocation_prefix"])
            self.border_ip = IPNetwork(self.simplified_json["border_auto_allocation_prefix"])
            self.customer_ip = IPNetwork(self.simplified_json["customer_auto_allocation_prefix"])

            self.bgp_auto_peering = self.simplified_json["bgp_auto_peering_asbr"]
            self.mpls_bgp_vpn = self.simplified_json["mpls_bgp_vpn"]

        self.internal_subnets = list(self.internal_ip.subnet(prefixlen=30, count=100))
        self.border_subnets = list(self.border_ip.subnet(prefixlen=30, count=100))
        self.customer_subnets = list(self.customer_ip.subnet(prefixlen=24, count=100))

    def handle_core_routers(self):
        template = open("./cisco/templates/core_routers_enrichment.json").read()
        for core in self.simplified_json["core_routers"]:
            self.enriched_json[core] = json.loads(template)
            for field in self.simplified_json["core_routers"][core]:
                if field == "ip_loopback":
                    self._add_loopback(core, self.simplified_json["core_routers"][core][field])
                else:
                    self._add_core_neighbor(core, field)

    def handle_edge_routers(self):
        template = open("./cisco/templates/edge_routers_enrichment.json").read()
        for edge in self.simplified_json["as_border_routers"]:
            self.enriched_json[edge] = json.loads(template)
            self.enriched_json[edge]["bgp"]["asn"] = str(self.simplified_json["asn_core"])
            for field in self.simplified_json["as_border_routers"][edge]:
                if field == "ip_loopback":
                    self._add_loopback(edge, self.simplified_json["as_border_routers"][edge][field])
                else:
                    self._add_edge_neighbor(edge, field)
        if self.bgp_auto_peering:
            self._config_bgp_on_edges()

    def handle_customer_routers(self):
        vpns_list = {}
        template = open("./cisco/templates/customer_routers_enrichment.json").read()
        for customer in self.simplified_json["customer_routers"]:
            self.enriched_json[customer] = json.loads(template)

            self.enriched_json[customer]["bgp"]["asn"] = str(self.as_id)
            self.as_id += 1

            for vpn in self.simplified_json["customer_routers"][customer]["vpn"]:
                if not vpn in vpns_list:
                    vpns_list[vpn] = []
                vpns_list[vpn].append(customer)

            for field in self.simplified_json["customer_routers"][customer]:
                if field == "ip_loopback":
                    self._add_loopback(customer, self.simplified_json["customer_routers"][customer][field])
                elif field == "vpn":
                    pass
                else:
                    self._add_customer_neighbor(customer, field)
        if self.mpls_bgp_vpn:
            self._config_vpns(vpns_list)

    def _add_loopback(self, router, ip_loopback):
        self.enriched_json[router]["interfaces"]["Loopback0"]["ipv4"] = ip_loopback + "/32"
        if "ospf" in self.enriched_json[router] and "network" in self.enriched_json[router]["ospf"]:
            self.enriched_json[router]["ospf"]["networks"][ip_loopback] = \
                {
                    "area": "0",
                    "mask": "0.0.0.0"
                }

    def _add_core_neighbor(self, router, neighbor_interface):
        ip = self._get_internal_subnet()
        self.enriched_json[router]["ospf"]["networks"][ip.split("/")[0]] = \
            {
                "area": "0",
                "mask": "0.0.0.3"
            }
        ip = IPNetwork(ip)
        ip.value += 1
        neighbor = self.simplified_json["core_routers"][router][neighbor_interface]
        self.enriched_json[router]["interfaces"][neighbor_interface] = \
            {
                "target_router": neighbor,
                "target_interface": neighbor_interface,
                "shutdown": False
            }

        if neighbor in self.enriched_json:
            for interface in self.enriched_json[neighbor]["interfaces"]:
                if interface != "Loopback0" and router in self.enriched_json[neighbor]["interfaces"][interface][
                    "target_router"]:
                    ip = IPNetwork(self.enriched_json[neighbor]["interfaces"][interface]["ipv4"])
                    ip.value += 1
                    self.enriched_json[router]["interfaces"][neighbor_interface]["ipv4"] = str(ip)
                    return
        self.enriched_json[router]["interfaces"][neighbor_interface]["ipv4"] = str(ip)

    def _add_edge_neighbor(self, router, neighbor_interface):
        neighbor = self.simplified_json["as_border_routers"][router][neighbor_interface]
        self.enriched_json[router]["interfaces"][neighbor_interface] = \
            {
                "target_router": neighbor,
                "target_interface": neighbor_interface,
                "shutdown": False
            }

        if neighbor in self.simplified_json["core_routers"]:
            self.enriched_json[router]["interfaces"][neighbor_interface]["mpls"] = "ip"

        if neighbor in self.simplified_json["as_border_routers"]:
            ip = self._get_internal_subnet()
            ip = IPNetwork(ip)
            ip.value += 1
        if neighbor in self.simplified_json["customer_routers"]:
            ip = self._get_border_subnet()
            ip = IPNetwork(ip)
            ip.value += 1
        else:
            for interface in self.enriched_json[neighbor]["interfaces"]:
                if "target_router" in self.enriched_json[neighbor]["interfaces"][interface]:
                    if self.enriched_json[neighbor]["interfaces"][interface]["target_router"] == router:
                        ip = self.enriched_json[neighbor]["interfaces"][interface]["ipv4"]
            self.enriched_json[router]["ospf"]["networks"][ip.split("/")[0]] = \
                {
                    "area": "0",
                    "mask": "0.0.0.255"
                }

        if neighbor in self.enriched_json:
            for interface in self.enriched_json[neighbor]["interfaces"]:
                if interface != "Loopback0" and router in self.enriched_json[neighbor]["interfaces"][interface][
                    "target_router"]:
                    ip = IPNetwork(self.enriched_json[neighbor]["interfaces"][interface]["ipv4"])
                    ip.value += 1
                    self.enriched_json[router]["interfaces"][neighbor_interface]["ipv4"] = str(ip)
                    return
        self.enriched_json[router]["interfaces"][neighbor_interface]["ipv4"] = str(ip)

    def _config_bgp_on_edges(self):
        for current_router in self.simplified_json["as_border_routers"]:
            for other_router in [router for router in self.simplified_json["as_border_routers"] if
                                 router != current_router]:
                ip_loopback = self.simplified_json["as_border_routers"][other_router]["ip_loopback"]
                self.enriched_json[current_router]["bgp"]["afis"]["ipv4_unicast"]["neighbors"] = \
                    {
                        ip_loopback:
                            {
                                "activate": True,
                                "next-hop-self": True
                            }
                    }
                self.enriched_json[current_router]["bgp"]["afis"]["vpnv4_unicast"]["neighbors"] = \
                    {
                        ip_loopback:
                            {
                                "activate": True,
                                "send-community": "extended"
                            }
                    }
                self.enriched_json[current_router]["bgp"]["neighbors"][ip_loopback] = \
                    {
                        "remote-as": str(self.simplified_json["asn_core"]),
                        "update-source": "Loopback0"
                    }

    def _add_customer_neighbor(self, router, neighbor_interface):
        neighbor = self.simplified_json["customer_routers"][router][neighbor_interface]
        self.enriched_json[router]["interfaces"][neighbor_interface] = \
            {
                "target_router": neighbor,
                "target_interface": neighbor_interface,
                "shutdown": False
            }
        if neighbor != "lan":
            for interface in self.enriched_json[neighbor]["interfaces"]:
                if "target_router" in self.enriched_json[neighbor]["interfaces"][interface]:
                    if self.enriched_json[neighbor]["interfaces"][interface]["target_router"] == router:
                        ip = self.enriched_json[neighbor]["interfaces"][interface]["ipv4"].split("/")[0]
                        self.enriched_json[router]["bgp"]["afis"]["ipv4_unicast"]["neighbors"][ip] = \
                            {
                                "activate": True,
                                "advertisement-interval": "5"
                            }
                        self.enriched_json[router]["bgp"]["neighbors"][ip] = \
                            {
                                "remote-as": self.enriched_json[neighbor]["bgp"]["asn"]
                            }
                        break

        if neighbor in self.enriched_json:
            for interface in self.enriched_json[neighbor]["interfaces"]:
                if interface != "Loopback0" and router in self.enriched_json[neighbor]["interfaces"][interface][
                    "target_router"]:
                    ip = IPNetwork(self.enriched_json[neighbor]["interfaces"][interface]["ipv4"])
                    ip.value += 1
                    self.enriched_json[router]["interfaces"][neighbor_interface]["ipv4"] = str(ip)
                    return
        ip = self._get_customer_subnet()
        ip = IPNetwork(ip)
        ip.value += 1
        self.enriched_json[router]["interfaces"][neighbor_interface]["ipv4"] = str(ip)

    def _config_vpns(self, vpns_list):
        for router in self.simplified_json["as_border_routers"]:
            for vpn in vpns_list:
                for customer_router in vpns_list[vpn]:
                    for field in self.simplified_json["as_border_routers"][router]:
                        if customer_router == self.simplified_json["as_border_routers"][router][field]:
                            neighbor_ip = ""
                            neighbor_as = self.enriched_json[customer_router]["bgp"]["asn"]

                            for interface in (i for i in self.enriched_json[router]["interfaces"] if i != "Loopback0"):
                                if self.enriched_json[router]["interfaces"][interface]["target_router"] \
                                        == customer_router:
                                    neighbor_ip = self.enriched_json[router]["interfaces"][interface]["ipv4"]

                            self.enriched_json[router]["bgp"]["vrfs"]["vpn{}".format(vpn)] = \
                                {
                                    "afi": "ipv4",
                                    "config": {
                                        "redistribute": "connected"
                                    },
                                    "neighbors": {
                                        neighbor_ip.split("/")[0]: {
                                            "activate": True,
                                            "advertisement-interval": "5",
                                            "as-override": True,
                                            "remote-as": neighbor_as
                                        }
                                    }
                                }

                            router_as = self.enriched_json[router]["bgp"]["asn"]
                            self.enriched_json[router]["vrfs"]["vpn{}".format(vpn)] = \
                                {
                                    "rd": "{}:{}".format(router_as, vpn),
                                    "route-target_export": "{}:{}".format(router_as, vpn),
                                    "route-target_import": "{}:{}".format(router_as, vpn)
                                }

                            self.enriched_json[router]["interfaces"][field]["vrf_forwarding"] = "vpn{}".format(vpn)
                            break

    def _get_internal_subnet(self):
        ip = str(self.internal_subnets[0])
        del self.internal_subnets[0]
        return ip

    def _get_border_subnet(self):
        ip = str(self.border_subnets[0])
        del self.border_subnets[0]
        return ip

    def _get_customer_subnet(self):
        ip = str(self.customer_subnets[0])
        return ip

    def export(self, file_path):
        with open(file_path, 'w') as outfile:
            json.dump(self.enriched_json, outfile, indent=4)
