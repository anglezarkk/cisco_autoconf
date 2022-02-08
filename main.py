import json

import cisco.config
import cisco.topology
import cisco.parser
import cisco.enrich


if __name__ == '__main__':
    # Dump config from GNS3
    # routers = cisco.config.get_routers_from_config()
    # cisco.config.dump(routers)

    # Topology analysis
    # topology = cisco.topology.Topology(routers)
    # topology.output_topology()

    enrich = cisco.enrich.Enrich("./config/simple.json")
    enrich.handle_cores()
    enrich.export("./config/test.json")
