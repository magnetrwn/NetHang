import socket as so
import random

from NetHang.run import temp_run_start, temp_run_stop


UTF8_DATA = "".join(tuple(chr(i) for i in range(32, 0x110000) if chr(i).isprintable()))

def generate_utf8_string(length):
    """Generate random strings using all UTF-8 characters available"""
    string = ""
    for _ in range(length):
        string += random.choices(UTF8_DATA)[0]
    return string


def test_bad_username_attempt():
    """Tests logging in with too long, too short and bad encoding (!latin-1) usernames"""
    port = random.randint(49152, 65535)
    temp_run = temp_run_start(port)
    username_length = 1
    conn = so.create_connection(("localhost", port))
    conn.settimeout(2)
    conn.recv(256)
    two_line_response = False
    for username_length in [1, 2, 15, 32, 33, 512]:
        for _ in range(6):
            conn.send(generate_utf8_string(username_length).encode("utf-8"))
            if two_line_response:
                conn.recv(256)
            if b"Nickname" not in conn.recv(256):
                # User was able to login with a bad username
                conn.close()
                temp_run_stop(temp_run)
                assert False
                return
            two_line_response = True

    conn.close()
    temp_run_stop(temp_run)
    assert True
