import json

from cisco.templates.enrichment import DEFAULT_CORE_DATA


class Enrich:
    simplified_json = {}
    enriched_json = {}
    mpls_bgp_vpn = False
    bgp_auto_peering = False

    def __init__(self, file_path):
        with open(file_path) as json_file:
            self.simplified_json = json.load(json_file)
            self.bgp_auto_peering = self.simplified_json["bgp_auto_peering_asbr"]
            self.mpls_bgp_vpn = self.simplified_json["mpls_bgp_vpn"]

    def handle_cores(self):
        for core in self.simplified_json["core_routers"]:
            self.enriched_json[core] = DEFAULT_CORE_DATA
            for field in self.simplified_json["core_routers"][core]:
                if field == "ip_loopback":
                    self._add_core_loopback(core, self.simplified_json["core_routers"][core][field])
                else:
                    self._add_core_neighbor(core, field)

    def _add_core_loopback(self, core, ip_loopback):
        self.enriched_json[core]["interfaces"]["Loopback0"]["ipv4"] = ip_loopback  # mask needed in simple
        self.enriched_json[core]["ospf"]["networks"][ip_loopback] = \
            {
                "area": "0",
                "mask": "0.0.0.0"
            }

    def _add_core_neighbor(self, core, neighbor_interface):
        self.enriched_json[core]["interfaces"][neighbor_interface] = \
            {
                "target_router": self.simplified_json["core_routers"][core][neighbor_interface],
                "target_interface": neighbor_interface,
                "shutdown": False
            }

    def export(self, file_path):
        with open(file_path, 'w') as outfile:
            json.dump(self.enriched_json, outfile, indent=4)
