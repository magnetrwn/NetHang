"""All tests related to possibly invalid, dirty or bad user input."""

# NetHang globally uses "latin-1" encoding, but maybe "utf-8" is better?
# Some tests check the user input with mismatching encoding.

import random
import socket as so
from time import sleep

import NetHang


ASCII_ALL = [chr(i) for i in range(128)]
LATIN1_PRINTABLE = [chr(i) for i in range(32, 256) if chr(i).isprintable()]
UTF8_PRINTABLE = [chr(i) for i in range(32, 0x110000) if chr(i).isprintable()]


def generate_string(length, charset=LATIN1_PRINTABLE):
    """Generate random strings of length characters using all UTF-8 characters available"""
    return "".join([random.choices(charset)[0] for _ in range(length)])


def new_server():
    port = random.randint(49152, 65535)
    return NetHang.server.HangmanServer(
        "localhost", priority_settings={"avail_ports": [port]}
    )


def recv_until(socket, bytestring):
    recv_buf = b""
    while bytestring not in recv_buf:
        recv_buf += socket.recv(1)
    return recv_buf


# ------------------------------ tests ------------------------------


def test_simple_user_joining():
    """Can a simple nickname join the server from localhost?"""
    try:
        server = new_server()
        server.run()
        with so.create_connection(("localhost", server.server_port)) as client:
            recv_until(client, b"Nickname: ")
            client.send(b"SimpleUserBestUser\n")

            # Check if reply is correct, or raise TimeoutError
            NetHang.util.timeout_in(1)
            recv_until(client, b"Welcome")
            NetHang.util.timeout_kill()

            client.shutdown(so.SHUT_RDWR)
        sleep(0.08)
        server.stop()

    except Exception:
        server.stop()
        raise

    assert True


def test_bad_name_length_joining():
    """Does the server block too long/short nicknames?"""
    try:
        server = new_server()
        server.run()
        with so.create_connection(("localhost", server.server_port)) as client:
            recv_until(client, b"Nickname: ")

            for nickname in [b"\n", b"A\n", b"Longlonglonglonglonglonglonglongl\n"]:
                client.send(nickname)

                # Check if reply shows reprompts user, or raise TimeoutError
                NetHang.util.timeout_in(1)
                recv_until(client, b"Nickname: ")
                NetHang.util.timeout_kill()

            client.shutdown(so.SHUT_RDWR)
        server.stop()

    except Exception:
        server.stop()
        raise

    assert True
