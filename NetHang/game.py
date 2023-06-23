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

    def _game_loop(self, players, commands_queue):
        print("_game_loop():", players.get_nicknames())
        print("_game_loop(): game started")
        sleep(6)
        print("_game_loop(): done")

    def start(self):
        if not self.is_alive():
            self.game_process = Process(
                target=self._game_loop, args=(self.players, self.commands_queue)
            )
            self.game_process.start()
        else:
            raise RuntimeError("Already started.")

    def stop(self):
        self.game_process.join(5)
        if self.game_process.is_alive():
            self.game_process.terminate()
            self.game_process.join()

    def is_alive(self):
        """Check if game has started."""
        if self.game_process is not None:
            return self.game_process.is_alive()
        return False

    def control(self):
        """Getter for control of the commands queue."""
        return self.commands_queue


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


# TODO: This file can be expanded with more games, not just related
#       to hangman! A project focus change is in order!
