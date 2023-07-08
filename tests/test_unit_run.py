"""Tests for the run.py module."""

import sys
import socket as so
from time import sleep


def recv_until(socket, bytestring):
    recv_buf = b""
    while bytestring not in recv_buf:
        recv_buf += socket.recv(1)
    return recv_buf


def test_running_from_cli(capfd):
    """Does the CLI entry point, as specified in setup.cfg, work?
    This will use the game_class setting in settings.json"""

    with capfd.disabled():
        print("\n--- TEST RUNNING FROM CLI ---")
        sys.argv = ["nethang", "localhost"]
        import NetHang

        try:
            cli_server = NetHang.run.cli_run()
            sleep(0.08)
            client = so.create_connection(("localhost", cli_server.server_port))
            try:
                recv_until(client, b"Nickname: ")
            finally:
                client.shutdown(so.SHUT_RDWR)
                client.close()
        finally:
            NetHang.run.cli_stop(cli_server)
        print("-----------------------------")
