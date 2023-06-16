import socket as so
import random

from NetHang.run import temp_run_start, temp_run_stop


UTF8_DATA = ''.join(tuple(chr(i) for i in range(32, 0x110000) if chr(i).isprintable()))

def generate_utf8_string(length):
    string = ""
    for _ in range(length):
        string += random.choices(UTF8_DATA)[0]
    return string


def test_user_joining():
    port = random.randint(49152, 65535)
    temp_run = temp_run_start(port)
    username_length = 1
    while username_length <= 4:
        for _ in range(1):
            conn = so.create_connection(("localhost", port))
            conn.settimeout(2)
            conn.recv(256)
            conn.send(generate_utf8_string(username_length).encode("utf-8"))
            if b"Nickname" not in conn.recv(256):
                assert False
            conn.close()
        username_length += username_length
    temp_run_stop(temp_run)
    assert True
