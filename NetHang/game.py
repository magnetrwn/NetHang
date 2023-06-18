"""Game classes, abstracted to the main components"""


# TODO: make it step by step, start by making sure all players can
#       enter and make them alternate the turn by writing something and sending it
class HangmanGame:
    """Base class for all turn-based hangman games."""
    # Player+data queue; playerlist for game

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
