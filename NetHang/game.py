"""Game classes, abstracted to the main components"""


from multiprocessing import Process, SimpleQueue

from NetHang.graphics import string_to_masked
from NetHang.players import PlayerList, send_all


class HangmanGame:
    """Base class for all turn-based hangman games."""

    def __init__(self, players=PlayerList()):
        self.players = players
        self.commands_queue = SimpleQueue()

        self.game_process = None

    # TODO: catching on KeyboardInterrupt'd server
    def _game_loop(self, players, commands_queue):
        send_all(players, "\x1B[01;36mGame started.\x1B[0m\n")
        hanger, prev_hanger = None, None
        for roundn in range(5):
            send_all(players, "Round " + str(roundn + 1) + ".\n")
            if players.count() < 2:
                send_all(players, "\x1B[01;36mNot enough players.\x1B[0m\n")
                return
            while hanger == prev_hanger:
                hanger = players.get_random_player()
            HangmanRound(hanger, players, commands_queue)
            prev_hanger = hanger
        send_all(players, "\x1B[01;36mGame ended.\x1B[0m\n")

    def start(self):
        """Start the game."""
        if not self.is_alive():
            self.game_process = Process(
                target=self._game_loop, args=(self.players, self.commands_queue)
            )
            self.game_process.start()
        else:
            raise RuntimeError("Already started.")

    def stop(self):
        """Stop the game."""
        self.game_process.join(5)
        if self.game_process.is_alive():
            self.game_process.terminate()
            self.game_process.join()

    def is_alive(self):
        """Check if game has started."""
        if self.game_process is not None:
            return self.game_process.is_alive()
        return False


class HangmanRound:
    """A single round of the turn-based hangman game."""

    def __init__(self, hanger, players, commands_queue):
        self.hanger = hanger
        self.players = players
        self.commands_queue = commands_queue

        self.guessers = players.copy()
        self.guessers.drop_player(nickname=hanger.nickname)

        self._round_loop()

    def _round_loop(self):
        # TODO: duplicate code from server.py
        send_all(
            self.guessers,
            "\x1B[01;36mWaiting for " + self.hanger.nickname + "...\x1B[0m\n",
        )
        for _ in range(10):
            self.hanger.socket.settimeout(1)
            try:
                while True:
                    dirty = self.hanger.socket.recv(512)
                    if not dirty:
                        break
            except TimeoutError:
                pass
            self.hanger.socket.settimeout(None)
            word = ""
            self.hanger.socket.send(
                "You are the hanger, type your word: ".encode("latin-1")
            )

            try:
                word = self.hanger.socket.recv(81)[:-1].decode("latin-1")
            except UnicodeDecodeError:
                self.hanger.socket.send(
                    "Please only use latin-1 characters!\n".encode("latin-1")
                )
                continue
            except BrokenPipeError:
                print("\x1B[01;91mBroken Pipe.\x1B[0m")
                return

            if len(word) < 2 or len(word) > 80:
                self.hanger.socket.send(
                    "Only between 2 and 80 characters!\n".encode("latin-1")
                )
                continue
            break

        send_all(self.guessers, string_to_masked(word, []) + "\n")


class HangmanTurn:
    """A single turn of the turn-based hangman game."""


# TODO: This file can be expanded with more games, not just related
#       to hangman! A project focus change is in order!
