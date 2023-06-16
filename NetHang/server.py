"""Contains HangmanServer, which runs the server"""


import socket as so
import sys
from multiprocessing import Process, SimpleQueue, Value, cpu_count
from select import select
from time import sleep

from NetHang.graphics import GRAPHICS
from NetHang.players import Player, PlayerList, generate_rejoin_code


# TODO: reduce complexity
class HangmanServer:
    """Contains all methods to run the game server for hangman."""

    def __init__(
        self,
        server_address,
        settings=None,
    ):
        self.server_process = None
        self.server_socket = so.socket(so.AF_INET, so.SOCK_STREAM)
        self.running = Value("B")
        self.running.value = 0

        if settings is None:
            settings = {}
        self.max_conn = settings.get("max_conn", 20)
        self.avail_ports = settings.get("avail_ports", [29111, 29112, 29113])
        self.allow_same_source_ip = settings.get("allow_same_source_ip", False)
        self.new_conn_processes = max(
            1, settings.get("new_conn_processes", min(4, cpu_count() - 1))
        )
        self.delay_factor = settings.get("delay_factor", 1)

        port_ok = False
        bind_tries = 0
        while not port_ok and bind_tries < len(self.avail_ports):
            try:
                port = self.avail_ports[bind_tries]
                bind_tries += 1
                self.server_socket.bind((server_address, port))
            except (PermissionError, OSError) as error:
                print("\x1B[31m" + error.args[1] + "\x1B[0m")
            else:
                port_ok = True
        if not port_ok:
            sys.exit("\x1B[31mCould not bind to socket!\x1B[0m")
        self.server_socket.listen(self.max_conn)
        print(
            "Running on [\x1B[36m"
            + server_address
            + ":"
            + str(port)
            + "\x1B[0m] with "
            + str(self.new_conn_processes)
            + " client workers, "
            + str(self.max_conn)
            + " total clients."
        )

    def accept_clients_worker(
        self, server_socket, players_read_queue, players_write_queue
    ):
        """Worker daemon process that accepts new client connections."""
        # TODO: stop extra processes on full capacity lobby
        while True:
            try:
                client_raw = server_socket.accept()
                sleep(0.5 * self.delay_factor)
                client_raw[0].send(GRAPHICS["title"].encode("utf-8"))
                worker_players = players_read_queue.get()
                if not self.allow_same_source_ip:
                    if worker_players.is_player(socket=client_raw[0]):
                        client_raw[0].send(
                            "This client IP is already in use!\n".encode("utf-8")
                        )
                        client_raw[0].close()
                        continue
                while True:
                    client_raw[0].settimeout(1)
                    try:
                        while True:
                            sleep(0.25 * self.delay_factor)
                            dirty = client_raw[0].recv(512)
                            if not dirty:
                                break
                    except TimeoutError:
                        pass
                    client_raw[0].settimeout(None)
                    client_nickname = ""
                    client_raw[0].send("Nickname: ".encode("utf-8"))
                    try:
                        client_nickname = client_raw[0].recv(35)[:-1].decode("utf-8")
                        if worker_players.is_player(nickname=client_nickname):
                            client_raw[0].send(
                                "This nickname is already in use!\n".encode("utf-8")
                                # TODO: allow reconnections for disconnected users
                                # "Rejoining as this user? Code: \n".encode("utf-8")
                            )
                            continue
                    except UnicodeDecodeError:
                        client_raw[0].send(
                            "Please only use valid UTF-8 characters!\n".encode("utf-8")
                        )
                        continue
                    if (
                        not client_nickname.isalnum()
                        or len(client_nickname) < 2
                        or len(client_nickname) > 32
                    ):
                        client_raw[0].send(
                            "Only alphanumeric between 2 and 32 characters!\n".encode(
                                "utf-8"
                            )
                        )
                        continue
                    break
                rejoin_code = generate_rejoin_code()
                players_write_queue.put(
                    Player(
                        client_raw[0],
                        client_nickname,
                        rejoin_code=rejoin_code,
                    )
                )
                client_raw[0].send(GRAPHICS["opening"].encode("utf-8"))
                client_raw[0].send(
                    (
                        "Your rejoin code is \x1B[01;91m" + rejoin_code + "\x1B[0m.\n\n"
                    ).encode("utf-8")
                )
                print("\x1B[36m" + client_nickname + " joined\x1B[0m")
            except BrokenPipeError:
                sleep(0.5 * self.delay_factor)
            except KeyboardInterrupt:
                return

    def run_worker(self, running):
        """Run the hangman server."""
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
                            decoded_data = data[:-1].decode("utf-8")
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
        print("\r\x1B[91mServer stopped.\x1B[0m")

    def run(self):
        """Run the hangman server."""
        self.running.value = 1
        self.server_process = Process(target=self.run_worker, args=(self.running,))
        self.server_process.start()

    def stop(self, *args):
        """Stop the hangman server."""
        self.running.value = 0
        self.server_process.join(5)
        if self.server_process.is_alive():
            self.server_process.terminate()
            self.server_process.join()
