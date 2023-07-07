"""Main program"""


import sys
from os import path

from NetHang.server import NetHangServer
from NetHang.util import load_json_dict


def cli_run():
    """Run server with YAML config, standard run option"""
    settings_path = path.join(
        path.dirname(path.abspath(__file__)), "config", "settings.json"
    )
    settings = load_json_dict(settings_path)

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

    module_name, class_name = settings["game_class"].rsplit(".", 1)
    imported_class = __import__(module_name, fromlist=[class_name])
    server = NetHangServer(
        host,
        game_class=getattr(imported_class, class_name),
        priority_settings=settings,
    )

    server.run()
    return server


def cli_stop(server):
    """Stop server"""
    server.stop()
