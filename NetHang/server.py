"""Contains HangmanServer, which runs the server"""


import socket as so
from os import path
from multiprocessing import Process, SimpleQueue, Value
from select import select
from time import sleep

from NetHang.graphics import GRAPHICS
from NetHang.players import Player, PlayerList, generate_rejoin_code
from NetHang.yaml import load_yaml_dict


# TODO: reduce complexity
# TODO: full convert to logging
class HangmanServer:
    """Contains all methods to run the game server for hangman."""

    def __init__(self, server_address, settings=None):
        # Loading settings.yaml
        configfile_path = path.join(
            path.dirname(path.abspath(__file__)), "config", "settings.yml"
        )
        configfile = load_yaml_dict(configfile_path)

        # For binding & listening new server socket -> setup_server()
        self.server_address = server_address
        self.server_port = None
        self.server_socket = None

        # For the underlying server process run -> run_worker()
        self.server_process = None
        self.running = Value("B", 0)

        # Extracting the server settings
        settings = settings or {}
        if settings == {} or not settings.get("enabled"):
            print("All default settings have been loaded.")
        self.max_conn = (
            settings.get("max_conn", configfile["default_max_conn"])
            if settings.get("enabled")
            else configfile["default_max_conn"]
        )
        self.avail_ports = (
            settings.get("avail_ports", configfile["default_avail_ports"])
            if settings.get("enabled")
            else configfile["default_avail_ports"]
        )
        self.allow_same_source_ip = (
            settings.get(
                "allow_same_source_ip", configfile["default_allow_same_source_ip"]
            )
            if settings.get("enabled")
            else configfile["default_allow_same_source_ip"]
        )
        self.new_conn_processes = (
            max(
                1,
                settings.get(
                    "new_conn_processes", configfile["default_new_conn_processes"]
                ),
            )
            if settings.get("enabled")
            else configfile["default_new_conn_processes"]
        )
        self.delay_factor = (
            settings.get("delay_factor", configfile["default_delay_factor"])
            if settings.get("enabled")
            else configfile["default_delay_factor"]
        )

        self.setup_server()

        print(
            "Init'd server on [\x1B[36m"
            + self.server_address
            + ":"
            + str(self.server_port)
            + "\x1B[0m] with "
            + str(self.new_conn_processes)
            + " client workers, "
            + str(self.max_conn)
            + " max clients."
        )

    def setup_server(self):
        """Binds the server instance defined address and port to a new server socket"""
        self.server_socket = so.socket(so.AF_INET, so.SOCK_STREAM)
        port_ok = False
        bind_tries = 0
        fatal = BaseException("Unknown exception caused server socket to fail bind!")

        while not port_ok and bind_tries < len(self.avail_ports):
            try:
                port = self.avail_ports[bind_tries]
                bind_tries += 1
                self.server_socket.bind((self.server_address, port))
            except Exception as error:
                print("\x1B[31m" + error.args[1] + "\x1B[0m")
                fatal = error
            else:
                port_ok = True

        if not port_ok:
            raise fatal

        self.server_socket.listen(self.max_conn)
        self.server_port = port

    def accept_clients_worker(
        self, server_socket, players_read_queue, players_write_queue
    ):
        """Worker daemon process that accepts new client connections."""
        # TODO: stop extra processes on full capacity lobby
        while True:
            try:
                client_socket, _ = server_socket.accept()
                sleep(0.5 * self.delay_factor)
                client_socket.send(GRAPHICS["title"].encode("latin-1"))
                worker_players = players_read_queue.get()

                if not self.allow_same_source_ip and worker_players.is_player(
                    socket=client_socket
                ):
                    client_socket.send(
                        "This client IP is already in use!\n".encode("latin-1")
                    )
                    client_socket.close()
                    continue

                while True:
                    client_socket.settimeout(1)
                    try:
                        while True:
                            sleep(0.25 * self.delay_factor)
                            dirty = client_socket.recv(512)
                            if not dirty:
                                break
                    except TimeoutError:
                        pass
                    client_socket.settimeout(None)
                    client_nickname = ""
                    client_socket.send("Nickname: ".encode("latin-1"))

                    try:
                        client_nickname = client_socket.recv(33)[:-1].decode("latin-1")
                        if worker_players.is_player(nickname=client_nickname):
                            client_socket.send(
                                "This nickname is already in use!\n".encode("latin-1")
                                # TODO: allow reconnections for disconnected users
                                # "Rejoining as this user? Code: \n".encode("latin-1")
                            )
                            continue
                    except UnicodeDecodeError:
                        client_socket.send(
                            "Please only use latin-1 characters!\n".encode("latin-1")
                        )
                        continue

                    if (
                        not client_nickname.isalnum()
                        or len(client_nickname) < 2
                        or len(client_nickname) > 32
                    ):
                        client_socket.send(
                            "Only alphanumeric between 2 and 32 characters!\n".encode(
                                "latin-1"
                            )
                        )
                        continue

                    break

                rejoin_code = generate_rejoin_code()
                players_write_queue.put(
                    Player(
                        client_socket,
                        client_nickname,
                        rejoin_code=rejoin_code,
                    )
                )
                client_socket.send(GRAPHICS["opening"].encode("latin-1"))
                client_socket.send(
                    (
                        "Your rejoin code is \x1B[01;91m" + rejoin_code + "\x1B[0m.\n\n"
                    ).encode("latin-1")
                )
                print("\x1B[36m" + client_nickname + " joined\x1B[0m")

            except BrokenPipeError:
                sleep(0.5 * self.delay_factor)
            except KeyboardInterrupt:
                return

    def run_worker(self, running):
        """Run the hangman server."""
        print("\r\x1B[36mServer process started.\n\x1B[0m")
        players = PlayerList()

        players_read_queue = SimpleQueue()
        players_write_queue = SimpleQueue()

        for _ in range(self.new_conn_processes):
            Process(
                target=self.accept_clients_worker,
                args=(self.server_socket, players_read_queue, players_write_queue),
                daemon=True,
            ).start()

        # TODO: add other ways to stop, like def kill()
        while bool(running.value):
            while not players_write_queue.empty():
                players.add_player(players_write_queue.get())
            while not players_read_queue.empty():
                players_read_queue.get()
            for _ in range(self.new_conn_processes):
                players_read_queue.put(players)

            try:
                ready_sockets = select(players.get_sockets(), [], [], 2)[0]
            except KeyboardInterrupt:
                running.value = 0
                break

            for socket in ready_sockets:
                player = players.get_player(socket=socket)
                try:
                    data = socket.recv(256)
                    if not data:
                        print("\x1B[36m" + player.nickname + " left\x1B[0m")
                        socket.close()
                        players.drop_player(nickname=player.nickname)
                    else:
                        try:
                            decoded_data = data[:-1].decode("latin-1")
                        except UnicodeDecodeError:
                            continue
                        # send tuple of (remote_ip, decoded data) to a queue read by
                        # a game loop process here...

                        print(
                            "\x1B[90m<" + player.nickname + ">:\x1B[0m " + decoded_data
                        )
                except ConnectionResetError:
                    print("\x1B[33m" + player.nickname + " reset connection.\x1B[0m")
                    socket.close()
                    players.drop_player(nickname=player.nickname)

        self.server_socket.close()
        print("\r\x1B[36mServer gracefully stopped.\n\x1B[0m")

    def run(self):
        """Run the hangman server."""
        self.running.value = 1
        self.server_process = Process(target=self.run_worker, args=(self.running,))
        self.server_process.start()
        print("\r\x1B[36mRunning server...\n\x1B[0m")

    def stop(self):
        """Stop the hangman server."""
        print("\r\x1B[36mStopping server...\n\x1B[0m")
        self.running.value = 0
        self.server_process.join(5)
        if self.server_process.is_alive():
            self.server_process.terminate()
            self.server_process.join()
