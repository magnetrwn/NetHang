"""Main program"""


import sys

from NetHang.server import HangmanServer


SETTINGS = {
    # Maximum number of concurrent users
    # "max_conn": 20,
    # Available ports to use, will only attach to one
    # "avail_ports": [29111, 29112, 29113],
    # Number of new user handlers, for concurrent user connection
    # "new_conn_processes": 10
    # Multiply all delays (mainly between queries from same user) by this value
    # "delay_factor": 1
    # Allow two or more users from the same source IP address
    "allow_same_source_ip": False
}


def cli_run():
    """Run server using CLI parameters, standard run option"""
    host = "localhost"
    if len(sys.argv) == 1:
        try:
            host = input("Type server IP: ")
        except KeyboardInterrupt:
            sys.exit()
    elif len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        sys.exit("\x1B[31mToo many arguments!\x1B[0m")

    HangmanServer(host, settings=SETTINGS).run()


def temp_run_start(port):
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


def temp_run_stop(server):
    """Stop temporary server on localhost"""
    server.stop()
