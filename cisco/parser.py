import ttp
import json


# BGP Cisco parser
def bgp(config):
    # Merge list of lines into string
    config = "\n".join(config)

    parser = ttp.ttp(data=config, template="cisco/templates/ios_bgp.txt")
    parser.parse()

    data = parser.result(format="json")

    return json.loads(data[0])


# OSPF Cisco parser
def ospf(config):
    config = "\n".join(config)

    parser = ttp.ttp(data=config, template="cisco/templates/ios_ospf.txt")
    parser.parse()

    data = parser.result(format="json")

    return json.loads(data[0])
