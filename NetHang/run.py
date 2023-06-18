"""Main program"""


import sys
from os import path

from NetHang.server import HangmanServer
from NetHang.yaml import load_yaml_dict


def cli_run():
    """Run server with YAML config, standard run option"""
    settings_path = path.join(
        path.dirname(path.abspath(__file__)), "config", "settings.yml"
    )
    settings = load_yaml_dict(settings_path)

    if settings.get("enabled") and settings.get("always_at") is not None:
        host = settings.get("always_at")
    else:
        if len(sys.argv) == 1:
            try:
                host = input("Type server address [localhost]: ")
            except KeyboardInterrupt:
                return
        elif len(sys.argv) == 2:
            host = sys.argv[1]
        else:
            raise TypeError("\x1B[31mInvalid number of arguments.\x1B[0m")

        if host == "":
            host = "localhost"

    server = HangmanServer(host, settings=settings if settings.get("enabled") else {})
    server.run()
    return server


def cli_stop(server):
    """Stop server"""
    server.stop()


def temp_run(port):
    """Run temporary server on localhost"""
    server = HangmanServer(
        "localhost",
        settings={
            "avail_ports": [port],
            "allow_same_source_ip": True,
            "delay_factor": 0,
        },
    )
    server.run()
    return server


def temp_stop(server):
    """Stop temporary server on localhost"""
    server.stop()
