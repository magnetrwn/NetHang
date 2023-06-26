"""Game classes, abstracted to the main components"""


from multiprocessing import Process, SimpleQueue

from NetHang.graphics import GRAPHICS, string_to_masked
from NetHang.players import PlayerList, send_all


def is_guessed(word, arr):
    """Check if the array has all of the word letters."""
    for _, strchar in enumerate(word):
        if not strchar.isalpha():
            continue
        if strchar not in arr:
            return False
    return True


class HangmanGame:
    """Base class for all turn-based hangman games."""

    def __init__(self, players=PlayerList(), rounds=5):
        self.players = players
        self.commands_queue = SimpleQueue()
        self.rounds = rounds
        self.game_process = None

    # TODO: catching on KeyboardInterrupt'd server
    def _game_loop(self, players, commands_queue):
        send_all(players, "\x1B[01;36mGame started.\x1B[0m\n")
        hanger, prev_hanger = None, None
        for round_ in range(self.rounds):
            send_all(
                players, "Round " + str(round_ + 1) + "/" + str(self.rounds) + ".\n"
            )
            if players.count() < 2:
                send_all(players, "\x1B[01;36mNot enough players.\x1B[0m\n")
                return
            while hanger == prev_hanger:
                hanger = players.get_random_player()
            HangmanRound(hanger, players, commands_queue, rounds=self.rounds)
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

    def __init__(self, hanger, players, commands_queue, rounds=5):
        self.hanger = hanger
        self.players = players
        self.rounds = rounds
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
        while True:
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

        send_all(self.players, GRAPHICS["clear"])
        send_all(
            self.players,
            "SCORE\n" + str(self.players.scoreboard()) + "\n\nLAST GUESS\n\n",
        )

        while self.fails <= 9 and not is_guessed(word, self.tried_letters):
            HangmanTurn(
                word,
                self.players,
                self.guessers,
                self.commands_queue,
                self.get_stats,
                self.update_stats,
            )

        send_all(
            self.players, '\n\n\n\x1B[01;36mThe word was "' + word + '"\x1B[0m\n\n\n'
        )

        if self.fails <= 9:
            send_all(self.players, "\n\x1B[01;92mGuessers win!\x1B[0m\n")
        else:
            send_all(self.players, "\n\x1B[01;91mGuessers lose!\x1B[0m\n")

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
                "\n\nGUESSWORD\n"
                + string_to_masked(self.word, self.tried_letters)
                + "\n",
            )

            send_all(
                self.players,
                "\nHANGER\n" + GRAPHICS["hangman" + str(self.fails)[0]] + "\n\n",
            )

            other_players = self.players.copy()
            other_players.drop_player(nickname=guesser.nickname)
            send_all(other_players, guesser.nickname + "'s guess...\n")
            # TODO: no memory leaks, right?

            guesser.socket.send(
                "\x1B[01;36mIt's your turn! Your guess: \x1B[0m".encode("latin-1")
            )

            # TODO: whole string guessing, not just letters
            while True:
                command = self.commands_queue.get()
                while command[0].nickname != guesser.nickname:
                    command[0].socket.send("Wait for your turn!\n".encode("latin-1"))
                    command = self.commands_queue.get()
                letter = command[1].lower()
                if len(letter) == 0 or len(letter) > 1:
                    guesser.socket.send("\n> ".encode("latin-1"))
                    continue
                break

            send_all(self.players, GRAPHICS["clear"])
            send_all(self.players, "SCORE\n" + str(self.players.scoreboard()) + "\n\n")

            # Assign weighted scoring for each guess
            if letter in self.tried_letters:
                self.fails += 1
                send_all(
                    self.guessers,
                    'LAST GUESS\n\x1B[01;36m"'
                    + letter.upper()
                    + '"\x1B[0m: \x1B[91mguessed already!\x1B[0m\n',
                )
                guesser.score -= 5 + (guesser.score // 10)
            elif letter not in self.word.lower():
                self.fails += 1
                send_all(
                    self.guessers,
                    'LAST GUESS\n\x1B[01;36m"'
                    + letter.upper()
                    + '"\x1B[0m: \x1B[91mno!\x1B[0m\n',
                )
                guesser.score -= 12 + (guesser.score // 20)
            else:
                send_all(
                    self.guessers,
                    'LAST GUESS\n\x1B[01;36m"'
                    + letter.upper()
                    + '"\x1B[0m: \x1B[92myes!\x1B[0m\n',
                )
                guesser.score += 50 // max(1, guesser.score // 500)

            if letter not in self.tried_letters:
                self.tried_letters.append(letter)

            self.update_stats(tried_letters=self.tried_letters, fails=self.fails)

            if self.fails == 10 or is_guessed(self.word, self.tried_letters):
                break


# TODO: This file can be expanded with more games, not just related
#       to hangman! A project focus change is in order!
