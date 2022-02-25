import json

import cisco.config
import cisco.topology
import cisco.parser
import cisco.enrich
import cisco.export


if __name__ == '__main__':
    # # Dump config from GNS3
    # routers = cisco.config.get_routers_from_config()
    # cisco.config.dump(routers)
    #
    # # Topology analysis
    # topology = cisco.topology.Topology(routers)
    # topology.output_topology()

    enrich = cisco.enrich.Enrich("./config/simple.json")
    enrich.handle_core_routers()
    enrich.handle_edge_routers()
    enrich.handle_customer_routers()
    enrich.export("./config/test.json")

    # routers = cisco.config.get_routers_from_config()
    # for router in routers:
    #     export = cisco.export.Export(router_name=router['name'], path='./config/test.json')
    #     export.generate_config()

