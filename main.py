import cisco.dump
import cisco.topology
import json
import ipaddress
from ciscoconfparse import CiscoConfParse

with open("routers.json", "r") as fp:
    routers = json.load(fp)

rout = []

for router in routers:
    rout.append(router["name"])
    #dumper = cisco.dump.Dump(router["name"], router["host"], router["port"])
    #dumper.write_running_config()

t = cisco.topology.Topology(rout)
interfaces = t.find_interfaces_connections()

print(interfaces)
t.output_topology()