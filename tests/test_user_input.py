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
    """Tests logging in with too long, too short or bad encoding usernames"""
    # TODO: this test does not make much sense, because the server accepts
    #       most unicode chars for users and there are no charset limits yet.
    #       Length checking is also problematic because of the buffer size,
    #       making consecutive requests of progressively shorter usernames.
    port = random.randint(49152, 65535)
    temp_run = temp_run_start(port)
    username_length = 1
    conn = so.create_connection(("localhost", port))
    conn.settimeout(2)
    conn.recv(256)
    two_line_response = False
    for username_length in [1, 33]:
        for _ in range(6):
            conn.send(generate_utf8_string(username_length).encode("utf-8"))
            if two_line_response:
                conn.recv(256)
            a=conn.recv(256)
            print(username_length, _, a)
            if b"Nickname" not in a:
                # User was able to login with a bad username
                assert False
            two_line_response = True

    conn.close()
    temp_run_stop(temp_run)
    assert True
