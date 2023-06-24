"""Contains HangmanServer, which runs the server"""


import socket as so
from os import path
from multiprocessing import Process, SimpleQueue, Value
from random import randint
from select import select
from time import sleep, time

from NetHang.game import HangmanGame, Command
from NetHang.graphics import GRAPHICS, should_countdown
from NetHang.players import Player, PlayerList, generate_rejoin_code
from NetHang.util import load_yaml_dict


def send_all(players, string, enc="latin-1"):
    """Send all sockets the same message."""
    for socket in players.get_sockets():
        socket.send(string.encode(enc))


# TODO: combo print + detail logging
class HangmanServer:
    """Contains all methods to run the game server for hangman."""

    def __init__(self, server_address, priority_settings=None, bypass_yaml=False):
        # For binding & listening new server socket -> _setup_server()
        self.server_address = server_address
        self.server_port = None
        self.server_socket = None

        # For the underlying server process run -> _run_worker()
        self.server_process = None
        self.running = Value("B", 0)

        self._setup_settings(priority_settings, bypass_yaml)
        self._setup_server()

        print(
            "Init'd server on [\x1B[36m"
            + self.server_address
            + ":"
            + str(self.server_port)
            + "\x1B[0m] with "
            + str(self.settings["new_conn_processes"])
            + " client workers, "
            + str(self.settings["max_conn"])
            + " max clients."
        )

    # TODO: make settings a class dict, not separate variables
    def _setup_settings(self, priority_settings, bypass_yaml):
        # Loading settings.yaml
        file_settings_path = path.join(
            path.dirname(path.abspath(__file__)), "config", "settings.yml"
        )

        # Extracting the server settings, parameter dict has priority on config file
        settings = load_yaml_dict(file_settings_path) if not bypass_yaml else {}
        settings.update(priority_settings or {})
        settings.update(
            {
                "new_conn_processes": max(
                    1,
                    settings.get("new_conn_processes"),
                )
            }
        )
        if settings.get("avail_ports") == "auto":
            settings.update({"avail_ports": [randint(49152, 65535) for _ in range(5)]})

        self.settings = settings

    def _setup_server(self):
        """Binds the server instance defined address and port to a new server socket"""
        self.server_socket = so.socket(so.AF_INET, so.SOCK_STREAM)
        port_ok = False
        bind_tries = 0
        fatal = BaseException("Unknown exception caused server socket to fail bind!")

        while not port_ok and bind_tries < len(self.settings["avail_ports"]):
            try:
                port = self.settings["avail_ports"][bind_tries]
                bind_tries += 1
                self.server_socket.bind((self.server_address, port))
            except Exception as error:
                print("\x1B[31m" + error.args[1] + "\x1B[0m")
                fatal = error
            else:
                port_ok = True

        if not port_ok:
            raise fatal

        self.server_socket.listen(self.settings["max_conn"])
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
                sleep(0.5 * self.settings["delay_factor"])
                client_socket.send(GRAPHICS["title"].encode("latin-1"))
                worker_players = players_read_queue.get()
                if not self.settings[
                    "allow_same_source_ip"
                ] and worker_players.is_player(address=client_address):
                    client_socket.send(
                        "This client IP is already in use!\n".encode("latin-1")
                    )
                    client_socket.close()
                    continue

                while True:
                    client_socket.settimeout(1)
                    try:
                        while True:
                            sleep(0.25 * self.settings["delay_factor"])
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
                if not self.settings[
                    "allow_same_source_ip"
                ] and worker_players.is_player(address=client_address):
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
                sleep(0.5 * self.settings["delay_factor"])
            except KeyboardInterrupt:
                return

    def _run_worker(self, running):
        """Run the hangman server."""
        print("\r\x1B[36mServer process started.\x1B[0m")
        players = PlayerList()

        players_read_queue = SimpleQueue()
        players_write_queue = SimpleQueue()

        for _ in range(self.settings["new_conn_processes"]):
            Process(
                target=self._accept_clients_worker,
                args=(self.server_socket, players_read_queue, players_write_queue),
                daemon=True,
            ).start()

        # TODO: add choice to manually start game, like in the readme import example
        game = HangmanGame()

        # start_timer determines if game is on or not:
        #   an integer if not, value is seconds countdown
        #   None if running
        start_timer = None

        while bool(running.value):
            # One second delay while waiting, but not ingame
            if start_timer is not None:
                try:
                    sleep(1 - time() % 1)
                except KeyboardInterrupt:
                    running.value = 0

            while not players_write_queue.empty():
                players.add_player(players_write_queue.get())
            while not players_read_queue.empty():
                players_read_queue.get()
            for _ in range(2 * self.settings["new_conn_processes"]):
                players_read_queue.put(players)

            if not game.is_alive():
                if start_timer is None:
                    # Game is done, new timer
                    start_timer = self.settings["lobby_time"]
                elif start_timer == 0:
                    # Game start
                    send_all(players, GRAPHICS["clear"])
                    game.players = players
                    game.start()
                    start_timer = None
                else:
                    # Countdown
                    if should_countdown(start_timer):
                        send_all(
                            players,
                            "\x1B[01;36mStarting in " + str(start_timer) + "\x1B[0m\n",
                        )
                    start_timer -= 1

            try:
                ready_sockets = select(
                    # No longer one second delay, now realtime (poll)
                    players.get_sockets(),
                    [],
                    [],
                    1 if start_timer is None else 0,
                )[0]
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

                        # Send received string of decoded data to the commands queue
                        # of the game process, which will queue all requests by
                        # time of reception
                        game.commands_queue.put(Command(player, decoded_data))

                        # send_all(
                        #     players,
                        #     "\x1B[90m<" + player.nickname + ">:\x1B[0m " + decoded_data,
                        # )
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
