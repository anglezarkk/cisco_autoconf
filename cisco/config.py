import json
import cisco.dump


def get_routers_from_config(filename = 'config/routers.json'):
    with open(filename, "r") as fp:
        routers = json.load(fp)

    return routers


def dump(routers):
    for router in routers:
        dumper = cisco.dump.Dump(router["name"], router["host"], router["port"])
        dumper.write_running_config()
