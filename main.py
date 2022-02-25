#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import cisco.enrich
import cisco.export

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate MPLS/BGP/VPN configuration for cisco routers,'
                                                 ' based on a simple json file.')
    parser.add_argument('--topology', required=True,
                        help='Path to simple json file')

    args = parser.parse_args()

    enrich = cisco.enrich.Enrich(str(args.topology))
    enrich.handle_core_routers()
    enrich.handle_edge_routers()
    enrich.handle_customer_routers()
    enrich.export("./config/export.json")

    for router in enrich.enriched_json:
        export = cisco.export.Export(router_name=router, path='./config/export.json')
        export.generate_config()

