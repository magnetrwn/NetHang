"""Contains HangmanServer, which runs the server"""


import socket as so
from os import path
from multiprocessing import Process, SimpleQueue, Value
from random import randint
from select import select
from time import sleep

from NetHang.game import HangmanGame
from NetHang.graphics import GRAPHICS
from NetHang.players import Player, PlayerList, generate_rejoin_code
from NetHang.yaml import load_yaml_dict


# TODO: combo print + detail logging
class HangmanServer:
    """Contains all methods to run the game server for hangman."""

    def __init__(self, server_address, settings=None):
        # Loading settings.yaml
        configfile_path = path.join(
            path.dirname(path.abspath(__file__)), "config", "settings.yml"
        )
        configfile = load_yaml_dict(configfile_path)

        # For binding & listening new server socket -> _setup_server()
        self.server_address = server_address
        self.server_port = None
        self.server_socket = None

        # For the underlying server process run -> _run_worker()
        self.server_process = None
        self.running = Value("B", 0)

        # Extracting the server settings, parameter dict has priority on config file
        settings = settings or {}
        self.max_conn = settings.get("max_conn", configfile["max_conn"])
        self.avail_ports = settings.get("avail_ports", configfile["avail_ports"])
        self.allow_same_source_ip = settings.get(
            "allow_same_source_ip", configfile["allow_same_source_ip"]
        )
        self.new_conn_processes = max(
            1,
            settings.get("new_conn_processes", configfile["new_conn_processes"]),
        )
        self.delay_factor = settings.get("delay_factor", configfile["delay_factor"])

        if self.avail_ports == "Auto":
            self.avail_ports = [randint(49152, 65535) for _ in range(5)]

        self._setup_server()

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

    def _setup_server(self):
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

    def _accept_clients_worker(
        self, server_socket, players_read_queue, players_write_queue
    ):
        """Worker daemon process that accepts new client connections."""
        while True:
            # TODO: stop extra processes on full capacity lobby
            try:
                client_socket, client_addr_port = server_socket.accept()
                client_address = client_addr_port[0]
                sleep(0.5 * self.delay_factor)
                client_socket.send(GRAPHICS["title"].encode("latin-1"))
                worker_players = players_read_queue.get()
                if not self.allow_same_source_ip and worker_players.is_player(
                    address=client_address
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

                # TODO: redundant, but needed to check if users have changed
                worker_players = players_read_queue.get()
                if not self.allow_same_source_ip and worker_players.is_player(
                    address=client_address
                ):
                    client_socket.send(
                        "This client IP is already in use!\n".encode("latin-1")
                    )
                    client_socket.close()
                    continue

                rejoin_code = generate_rejoin_code()
                players_write_queue.put(
                    Player(
                        client_socket,
                        client_nickname,
                        address=client_address,
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

    def _run_worker(self, running):
        """Run the hangman server."""
        print("\r\x1B[36mServer process started.\x1B[0m")
        players = PlayerList()

        players_read_queue = SimpleQueue()
        players_write_queue = SimpleQueue()

        for _ in range(self.new_conn_processes):
            Process(
                target=self._accept_clients_worker,
                args=(self.server_socket, players_read_queue, players_write_queue),
                daemon=True,
            ).start()

        # TODO: add choice to manually start game, like in the readme import example
        game = HangmanGame()
        start_timer = None

        while bool(running.value):
            sleep(1)

            while not players_write_queue.empty():
                players.add_player(players_write_queue.get())
            while not players_read_queue.empty():
                players_read_queue.get()
            for _ in range(2 * self.new_conn_processes):
                players_read_queue.put(players)

            # Two game states, will sleep when not running
            print("game.is_alive():", game.is_alive())
            game.players = players
            if not game.is_alive():
                if start_timer == 0:
                    game.start()
                    start_timer = None
                elif start_timer is None:
                    start_timer = 30
                else:
                    start_timer -= 1

            if start_timer is not None and start_timer % 10 == 0:
                for socket in players.get_sockets():
                    socket.send(
                        (
                            "\x1B[01;36mStarting in " + str(start_timer) + "\x1B[0m\n"
                        ).encode("latin-1")
                    )

            try:
                ready_sockets = select(players.get_sockets(), [], [], 0)[0]
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
        self.server_process = Process(target=self._run_worker, args=(self.running,))
        self.server_process.start()
        print("\r\x1B[36mRunning server...\x1B[0m")

    def stop(self):
        """Stop the hangman server."""
        print("\r\x1B[36mStopping server...\x1B[0m")
        self.running.value = 0
        self.server_process.join(5)
        if self.server_process.is_alive():
            self.server_process.terminate()
            self.server_process.join()
