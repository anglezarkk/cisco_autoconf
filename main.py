import cisco.dump
import cisco.topology
import ipaddress
from ciscoconfparse import CiscoConfParse

NAME = "R1"
HOST = "10.0.0.1"
PASSWORD = "cisco"

#dump=cisco.dump.Dump(NAME, HOST, PASSWORD, 0)

dumpR1 = cisco.dump.Dump("R1", "10.0.0.1", PASSWORD, 0)
dumpR2 = cisco.dump.Dump("R2", "10.0.0.2", PASSWORD, 0)
#dumpR1.write_running_config()
#dumpR2.write_running_config()
#dump.write_running_config()

t = cisco.topology.Topology(["R1", "R2"])
interfaces = t.find_interfaces_connections()

print(interfaces)
t.output_topology()