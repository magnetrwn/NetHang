""". HANGMAN NETCAT GAME SERVER:
| This file is a compact, client-server Python application to play
| hangman using netcat (nc), written for linux systems.
| ... TODO extend module docstring ...
'
"""
# TODO: extend module docstring
# TODO: state client terminal min width: 48 chars


#######################################
#                                     #
#        Setup globals/imports        #
#                                     #
#######################################


import socket as so
import sys
from multiprocessing import Process, SimpleQueue, cpu_count
from random import randint
from select import select
from time import sleep

STATIC_GRTEXT = {
    "clear": "\033[2J\033[H",
    "title": "\033[2J\033[H\x1B[01;36m ============= Welcome to Hangman =============\x1B[0m  \n",
    "opening": """\nWelcome to the game of Hangman on command line!
This implementation allows multiple players to
play different versions of the game, which are:\n
 \x1B[01;36ma.\x1B[0m Round-robin writer, rotating the player who
    writes the guessword after each turn;\n
 \x1B[01;36mb.\x1B[0m King of the hill, where the first to guess
    the word correctly becomes the writer;\n
 \x1B[01;36mc.\x1B[0m Wordlist, where there is no writer and the
    guessword is taken from a wordlist instead;\n
 \x1B[01;36md.\x1B[0m Time attack wordlist, the fastest of the
    gamemodes, in which there are no turns and
    guesses be given very quickly.\n
You can \x1B[01;36mquit\x1B[0m at any moment with \x1B[01;36m^C\x1B[0m (Ctrl-C).\n\n""",
    "hangman0": """






         [ 0/9     ]
""",
    "hangman1": """

|
|
|
|
|
|        [\x1B[07;36m \x1B[0m1/9     ]
""",
    "hangman2": """
 ____
/
|
|
|
|
|
|        [\x1B[07;36m 2\x1B[0m/9     ]
""",
    "hangman3": """
 ____
/   |
|
|
|
|
|
|        [\x1B[07;36m 3/\x1B[0m9     ]
""",
    "hangman4": """
 ____
/   |
|  ( )
|
|
|
|
|        [\x1B[07;36m 4/9\x1B[0m     ]
""",
    "hangman5": """
 ____
/   |
|  ( )
|   |
|   |
|   |
|
|        [\x1B[07;36m 5/9 \x1B[0m    ]
""",
    "hangman6": """
 ____
/   |
|  ( )
|  /|
| / |
|   |
|
|        [\x1B[07;36m 6/9  \x1B[0m   ]
""",
    "hangman7": """
 ____
/   |
|  ( )
|  /|\\
| / | \\
|   |
|
|        [\x1B[07;36m 7/9   \x1B[0m  ]
""",
    "hangman8": """
 ____
/   |
|  ( )
|  /|\\
| / | \\
|   |
|  /
| /      [\x1B[07;36m 8/9    \x1B[0m ]
""",
    "hangman9": """
 ____
/   |
|  ( )
|  /|\\
| / | \\
|   |
|  / \\
| /   \\  [\x1B[07;36m 9/9     \x1B[0m]
""",
}


def string_to_masked(string, to_show):
    """Return the input string wrapped, colorized and masked."""
    out = ""
    for i, strchar in enumerate(string):
        if (i + 1) % 48 == 0:
            out += "-\n-"
        if strchar in to_show or not strchar.isalpha():
            out += "\x1B[01;36m" + strchar + "\x1B[0m"
        else:
            out += "."
    return out


def generate_rejoin_code():
    """Generates a four number code, possibly with leading zeros."""
    return str(randint(0, 9999)).zfill(4)


#########################################
#                                       #
#        PlayerList: all classes        #
#                                       #
#########################################


class PlayerList:
    """List of all players, using the Player class."""

    def __init__(self):
        self.player_list = []

    def is_player(self, nickname=None, socket=None):
        """Check if there is a player with a certain nickname or socket."""
        if nickname is not None:
            for player in self.player_list:
                if player.nickname == nickname:
                    return True
            return False
        if socket is not None:
            for player in self.player_list:
                if player.socket == socket:
                    return True
            return False
        return False

    def get_player(self, nickname=None, socket=None):
        """Get a player by nickname or socket."""
        if nickname is not None:
            for player in self.player_list:
                if player.nickname == nickname:
                    return player
            return None
        if socket is not None:
            for player in self.player_list:
                if player.socket == socket:
                    return player
            return None
        return None

    def get_sockets(self):
        """Get a list of all player sockets."""
        return [player.socket for player in self.player_list]

    def get_nicknames(self):
        """Get a list of all player nicknames."""
        return [player.nickname for player in self.player_list]

    def add_player(self, player):
        """Add a player of Player type."""
        self.player_list.append(player)

    def drop_player(self, nickname=None, socket=None):
        """Drop a player by nickname or socket."""
        if nickname is not None:
            for i, player in enumerate(self.player_list):
                if player.nickname == nickname:
                    del self.player_list[i]
                    break
        if socket is not None:
            for i, player in enumerate(self.player_list):
                if player.socket == socket:
                    del self.player_list[i]
                    break


class Player:
    """Each Player combines a socket and a nickname."""

    def __init__(self, socket, nickname, rejoin_code=None):
        self.socket = socket
        self.nickname = nickname
        if rejoin_code is None:
            self.rejoin_code = generate_rejoin_code()
        else:
            self.rejoin_code = rejoin_code


############################################
#                                          #
#        HangmanServer: all classes        #
#                                          #
############################################


# TODO: reduce complexity
class HangmanServer:
    """Contains all methods to run the game server for hangman."""

    def __init__(
        self,
        server_address,
        settings=None,
    ):
        self.server_socket = so.socket(so.AF_INET, so.SOCK_STREAM)

        if settings is None:
            settings = {}
        self.max_conn = settings.get("max_conn", 20)
        self.avail_ports = settings.get("avail_ports", [29111, 29112, 29113])
        self.allow_same_source_ip = settings.get("allow_same_source_ip", False)
        self.new_conn_processes = max(
            1, settings.get("new_conn_processes", min(4, cpu_count() - 1))
        )

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
        self.players = PlayerList()

    def accept_clients_worker(
        self, server_socket, players_read_queue, players_write_queue
    ):
        """Worker daemon process that accepts new client connections."""
        # TODO: stop extra processes on full capacity lobby
        while True:
            try:
                client_raw = server_socket.accept()
                sleep(0.5)
                client_raw[0].send(STATIC_GRTEXT["title"].encode("utf-8"))
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
                            sleep(0.25)
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
                            "Please only use UTF-8 characters!\n".encode("utf-8")
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
                client_raw[0].send(STATIC_GRTEXT["opening"].encode("utf-8"))
                client_raw[0].send(
                    (
                        "Your rejoin code is \x1B[01;91m" + rejoin_code + "\x1B[0m.\n\n"
                    ).encode("utf-8")
                )
                print("\x1B[36m" + client_nickname + " joined\x1B[0m")
            except BrokenPipeError:
                sleep(0.5)
            except KeyboardInterrupt:
                return

    def run(self):
        """Run the hangman server."""
        players_read_queue = SimpleQueue()
        players_write_queue = SimpleQueue()

        for _ in range(self.new_conn_processes):
            Process(
                target=HangmanServer.accept_clients_worker,
                args=(
                    self,
                    self.server_socket,
                    players_read_queue,
                    players_write_queue,
                ),
                daemon=True,
            ).start()

        while True:
            while not players_write_queue.empty():
                self.players.add_player(players_write_queue.get())
            while not players_read_queue.empty():
                players_read_queue.get()
            for _ in range(self.new_conn_processes):
                players_read_queue.put(self.players)

            try:
                ready_sockets = select(self.players.get_sockets(), [], [], 2)[0]
            except KeyboardInterrupt:
                self.server_socket.close()
                sys.exit("\r\x1B[90mKeyboardInterrupt\x1B[0m")

            for socket in ready_sockets:
                player = self.players.get_player(socket=socket)
                try:
                    data = socket.recv(256)
                    if not data:
                        print("\x1B[36m" + player.nickname + " left\x1B[0m")
                        socket.close()
                        self.players.drop_player(nickname=player.nickname)
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
                    print("\x1B[33m" + player.nickname + " reset connection\x1B[0m")
                    socket.close()
                    self.players.drop_player(nickname=player.nickname)

        # TODO: what about self.server_socket.close()


##########################################
#                                        #
#        HangmanGame: all classes        #
#                                        #
##########################################


# TODO: make it step by step, start by making sure all players can
#       enter and make them alternate the turn by writing something and sending it
class HangmanGame:
    """Base class for all turn-based hangman games."""


class RoundRobinGame(HangmanGame):
    """Round-robin hangman gamemode."""


class KingHillGame(HangmanGame):
    """King of the hill hangman gamemode."""


class WordlistGame(HangmanGame):
    """Wordlist hangman gamemode."""


class Round:
    """A single round of the turn-based hangman game."""


class Turn:
    """A single turn of the turn-based hangman game."""


class TimeAttackGame:
    """Time attack hangman gamemode, not turn-based."""


class TimeAttackRound:
    """A single round of the time attack version hangman game."""


##########################
#                        #
#        __main__        #
#                        #
##########################


if __name__ == "__main__":
    HOST = "localhost"
    if len(sys.argv) == 1:
        try:
            HOST = input("Type server IP: ")
        except KeyboardInterrupt:
            sys.exit()
    elif len(sys.argv) == 2:
        HOST = sys.argv[1]
    else:
        sys.exit("\x1B[31mToo many arguments!\x1B[0m")

    HangmanServer(HOST, settings={"allow_same_source_ip": False}).run()
