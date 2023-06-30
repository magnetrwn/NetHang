"""Main program"""


import sys
from os import path

from NetHang.server import NetHangServer
from NetHang.util import load_yaml_dict


def cli_run():
    """Run server with YAML config, standard run option"""
    settings_path = path.join(
        path.dirname(path.abspath(__file__)), "config", "settings.yml"
    )
    settings = load_yaml_dict(settings_path)

    if settings.get("always_at") is not None:
        host = settings.get("always_at")
    else:
        if len(sys.argv) == 1:
            host = input("Type server address [localhost]: ")
        elif len(sys.argv) == 2:
            host = sys.argv[1]
        else:
            raise IndexError("Invalid number of arguments.")

        if host == "":
            host = "localhost"

    server = NetHangServer(host, priority_settings=settings)
    server.run()
    return server


def cli_stop(server):
    """Stop server"""
    server.stop()
