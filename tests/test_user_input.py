"""All tests related to possibly invalid, dirty or bad user input."""

# NetHang globally uses "latin-1" encoding, but maybe "utf-8" is better?
# Some tests check the user input with mismatching encoding.
# Testing sets the "hangman" GAME_DATA (from hangman.json), but tests the server only.
#  -> because of this, some bytestrings might belong to a game example.

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
    return NetHang.server.NetHangServer(
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


def test_user_rejoining():
    """Can the rejoin code be used to rejoin as user?"""
    try:
        server = new_server()
        server.run()

        first_client = so.create_connection(("localhost", server.server_port))
        recv_until(first_client, b"Nickname: ")
        first_client.send(b"RejoinUser\n")

        # Get rejoin code, or raise TimeoutError
        NetHang.util.timeout_in(1)
        rejoin_code = (
            recv_until(first_client, b"Lobby")
            .split(b"\x1B[01;91m", 1)[1]
            .split(b"\x1B[0m", 1)[0]
            .decode("latin-1")
        )
        NetHang.util.timeout_kill()
        sleep(0.08)

        with so.create_connection(("localhost", server.server_port)) as second_client:
            recv_until(second_client, b"Nickname: ")
            second_client.send(b"RejoinUser\n")

            # Rejoin, or raise TimeoutError
            NetHang.util.timeout_in(1)
            recv_until(second_client, b"Code: ")
            second_client.send(str(rejoin_code).encode("latin1") + b"\n")
            recv_until(second_client, b"Welcome back!")
            NetHang.util.timeout_kill()

            second_client.shutdown(so.SHUT_RDWR)
        sleep(0.08)
        server.stop()

    except Exception:
        first_client.close()
        server.stop()
        raise

    assert True


def test_user_chat_communication():
    """Can two users chat?"""
    n_messages = 6
    try:
        message_bytes = [
            generate_string(length).encode("latin1") + b"\n"
            for length in range(1, 4 * n_messages + 1, 4)
        ]
        server = new_server()
        server.run()
        with so.create_connection(
            ("localhost", server.server_port)
        ) as first_client, so.create_connection(
            ("localhost", server.server_port)
        ) as second_client:
            recv_until(first_client, b"Nickname: ")
            recv_until(second_client, b"Nickname: ")
            first_client.send(b"PlayerOne\n")
            second_client.send(b"PlayerTwo\n")

            # Check chat communication is correct, or raise TimeoutError (from recv_until stuck)
            NetHang.util.timeout_in(3)
            recv_until(first_client, b"1 minute\x1B[0m.\n")
            recv_until(second_client, b"1 minute\x1B[0m.\n")
            for i in range(n_messages):
                first_client.send(message_bytes[i])
                recv_until(second_client, message_bytes[i])
                sleep(0.04)
                second_client.send(message_bytes[i])
                recv_until(first_client, message_bytes[i])
                sleep(0.04)
            NetHang.util.timeout_kill()

            first_client.shutdown(so.SHUT_RDWR)
            second_client.shutdown(so.SHUT_RDWR)
        sleep(0.08)
        server.stop()

    except Exception:
        first_client.close()
        second_client.close()
        server.stop()
        raise

    assert True
