import json

from netaddr import IPNetwork


class Enrich:
    simplified_json = {}
    enriched_json = {}
    internal_subnets = ""
    customer_subnets = ""
    mpls_bgp_vpn = False
    bgp_auto_peering = False

    def __init__(self, file_path):
        with open(file_path) as json_file:
            self.simplified_json = json.load(json_file)
            internal_ip = IPNetwork(self.simplified_json["internal_auto_allocation_prefix"])
            customer_ip = IPNetwork(self.simplified_json["customer_auto_allocation_prefix"])
            self.bgp_auto_peering = self.simplified_json["bgp_auto_peering_asbr"]
            self.mpls_bgp_vpn = self.simplified_json["mpls_bgp_vpn"]

        self.internal_subnets = list(internal_ip.subnet(prefixlen=30, count=100))
        self.customer_subnets = list(customer_ip.subnet(prefixlen=24, count=100))

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
            self.enriched_json[edge]["bgp"]["asn"] = self.simplified_json["asn_core"]
            for field in self.simplified_json["as_border_routers"][edge]:
                if field == "ip_loopback":
                    self._add_loopback(edge, self.simplified_json["as_border_routers"][edge][field])
                else:
                    self._add_edge_neighbor(edge, field)
        self._config_bgp_on_edges()

    def _add_loopback(self, router, ip_loopback):
        self.enriched_json[router]["interfaces"]["Loopback0"]["ipv4"] = ip_loopback + "/32"
        if "network" in self.enriched_json[router]["ospf"]:
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
                "mask": "0.0.0.255"
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

        if neighbor in self.simplified_json["as_border_routers"]:
            ip = self._get_internal_subnet()
            ip = IPNetwork(ip)
            ip.value += 1
        if neighbor in self.simplified_json["customer_routers"]:
            ip = self._get_customer_subnet()
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
                self.enriched_json[current_router]["neighbors"][ip_loopback] = \
                    {
                        "remote-as": self.simplified_json["asn_core"],
                        "update-source": "Loopback0"
                    }

    def _get_internal_subnet(self):
        ip = str(self.internal_subnets[0])
        del self.internal_subnets[0]
        return ip

    def _get_customer_subnet(self):
        ip = str(self.customer_subnets[0])
        del self.customer_subnets[0]
        return ip

    def export(self, file_path):
        with open(file_path, 'w') as outfile:
            json.dump(self.enriched_json, outfile, indent=4)
