"""Game classes, abstracted to the main components"""


from time import sleep
from multiprocessing import Process, SimpleQueue

from NetHang.players import PlayerList


class Command:
    """Each command combines a Player with a command string."""

    def __init__(self, player, value):
        self.player = player
        self.value = value


class HangmanGame:
    """Base class for all turn-based hangman games."""

    def __init__(self, players=PlayerList()):
        self.players = players
        self.commands_queue = SimpleQueue()

        self.game_process = None

    # TODO: catching on KeyboardInterrupt'd server
    def _game_loop(self, players, commands_queue):
        hanger, prev_hanger = None, None
        for _ in range(5):
            if players.count() > 1:
                while hanger == prev_hanger:
                    hanger = players.get_random_player()
            HangmanRound(hanger, players, commands_queue)
            prev_hanger = hanger

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
        pass


class HangmanTurn:
    """A single turn of the turn-based hangman game."""


# TODO: This file can be expanded with more games, not just related
#       to hangman! A project focus change is in order!
