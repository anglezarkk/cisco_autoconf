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
