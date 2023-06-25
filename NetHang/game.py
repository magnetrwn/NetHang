"""Game classes, abstracted to the main components"""


from multiprocessing import Process, SimpleQueue

from NetHang.graphics import GRAPHICS, string_to_masked
from NetHang.players import PlayerList, send_all


class HangmanGame:
    """Base class for all turn-based hangman games."""

    def __init__(self, players=PlayerList(), options=(5, 10)):
        self.players = players
        self.commands_queue = SimpleQueue()
        self.options = options  # (rounds, turns)
        self.game_process = None

    # TODO: catching on KeyboardInterrupt'd server
    def _game_loop(self, players, commands_queue):
        send_all(players, "\x1B[01;36mGame started.\x1B[0m\n")
        hanger, prev_hanger = None, None
        for nround in range(self.options[0]):
            send_all(
                players, "Round " + str(nround + 1) + "/" + str(self.options[0]) + ".\n"
            )
            if players.count() < 2:
                send_all(players, "\x1B[01;36mNot enough players.\x1B[0m\n")
                return
            while hanger == prev_hanger:
                hanger = players.get_random_player()
            HangmanRound(hanger, players, commands_queue, options=self.options)
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

    def __init__(self, hanger, players, commands_queue, options=(5, 10)):
        self.hanger = hanger
        self.players = players
        self.options = options
        self.commands_queue = commands_queue

        self.tried_letters = []
        self.fails = 0

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

            try:
                self.hanger.socket.send(
                    "You are the hanger, type your word: ".encode("latin-1")
                )
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

        for nturn in range(self.options[1]):
            send_all(
                self.players,
                "Turn " + str(nturn + 1) + "/" + str(self.options[1]) + ".\n",
            )
            HangmanTurn(
                word,
                self.players,
                self.guessers,
                self.commands_queue,
                self.get_stats,
                self.update_stats,
            )

    def get_stats(self):
        """Pass this function to turn to give stats."""
        return (self.tried_letters, self.fails)

    def update_stats(self, tried_letters=None, fails=None):
        """Pass this function to turn to enable stats updates by turn."""
        if tried_letters is not None:
            self.tried_letters = tried_letters
        if fails is not None:
            self.fails = fails


class HangmanTurn:
    """A single turn of the turn-based hangman game, where all guessers guess."""

    def __init__(
        self, word, players, guessers, commands_queue, get_stats, update_stats
    ):
        self.word = word
        self.players = players
        self.guessers = guessers
        self.tried_letters, self.fails = get_stats()
        self.commands_queue = commands_queue
        self.update_stats = update_stats

        self._turn_loop()

    def _turn_loop(self):
        for guesser in self.guessers.player_list:
            send_all(
                self.players,
                "\n\n" + string_to_masked(self.word, self.tried_letters) + "\n",
            )

            send_all(
                self.players,
                GRAPHICS["hangman" + str(self.fails)] + "\n\n",
            )

            other_guessers = self.guessers.copy()
            other_guessers.drop_player(nickname=guesser.nickname)
            send_all(other_guessers, guesser.nickname + "'s guess.\n")
            # TODO: no memory leaks, right? :3

            guesser.socket.send(
                "\x1B[01;36mIt's your turn! Your guess: \x1B[0m".encode("latin-1")
            )
            letter = guesser.socket.recv(2)[-1].decode("latin-1")
            letter = letter.lower()
            if letter not in self.tried_letters:
                self.tried_letters.append(letter)
                send_all(
                    self.guessers,
                    '\x1B[01;36m"' + letter.upper() + '"\x1B[0m: guessed already!',
                )
            elif letter not in self.word.lower():
                self.fails += 1
                send_all(
                    self.guessers, '\x1B[01;36m"' + letter.upper() + '"\x1B[0m: no!'
                )
            else:
                send_all(
                    self.guessers, '\x1B[01;36m"' + letter.upper() + '"\x1B[0m: yes!'
                )

            self.update_stats(tried_letters=self.tried_letters, fails=self.fails)


# TODO: This file can be expanded with more games, not just related
#       to hangman! A project focus change is in order!
