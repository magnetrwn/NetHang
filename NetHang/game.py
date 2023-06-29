"""Game classes, abstracted to the main components"""


from multiprocessing import Process, SimpleQueue

from NetHang.graphics import GRAPHICS, string_to_masked
from NetHang.players import PlayerList, send_all
from NetHang.util import timeout_in, timeout_kill


def is_guessed(word, arr):
    """Check if the array has all of the word letters."""
    for _, strchar in enumerate(word.lower()):
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
        try:
            send_all(
                self.guessers,
                "\x1B[01;36mWaiting for " + self.hanger.nickname + "...\x1B[0m\n",
            )

            self.hanger.socket.send(
                "You are the hanger, type the guessword: ".encode("latin-1")
            )

            while True:
                command = self.commands_queue.get()
                while command[0].nickname != self.hanger.nickname:
                    if command[0].nickname == ".":
                        if command[1][0] == "-":
                            return
                    command = self.commands_queue.get()
                word = command[1]
                if len(word) < 2 or len(word) > 80:
                    self.hanger.socket.send(
                        "Between 2 and 80 characters only:  ".encode("latin-1")
                    )
                    continue
                break

            send_all(self.players, GRAPHICS["clear"])
            send_all(
                self.players,
                "\x1B[01;36mSCORE\x1B[0m\n"
                + str(self.players.scoreboard())
                + "\n\n\x1B[01;36mLAST GUESS\x1B[0m\n\n",
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
                self.players,
                '\n\n\n\x1B[01;36mThe word was "' + word + '"\x1B[0m\n\n\n',
            )

            if self.fails <= 9:
                send_all(self.players, "\n\x1B[01;92mGuessers win!\x1B[0m\n")
            else:
                send_all(self.players, "\n\x1B[01;91mGuessers lose!\x1B[0m\n")

        except (BrokenPipeError, BlockingIOError):
            print("\x1B[01;91mUnavailable socket. Stopping ongoing game.\x1B[0m")
            send_all(
                self.players,
                "\n\x1B[01;91mUnavailable socket. Stopping ongoing game.\n\x1B[0m",
            )
            return

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
                "\n\x1B[01;36mGUESSWORD\x1B[0m\n"
                + string_to_masked(self.word, self.tried_letters)
                + "\n",
            )

            send_all(
                self.players,
                "\n\x1B[01;36mHANGER\x1B[0m\n"
                + GRAPHICS["hangman" + str(self.fails)[0]]
                + "\n\n",
            )

            other_players = self.players.copy()
            other_players.drop_player(nickname=guesser.nickname)
            send_all(other_players, guesser.nickname + "'s guess...\n")

            guesser.socket.send(
                "\x1B[01;36mIt's your turn! You have 60 seconds: \x1B[0m".encode(
                    "latin-1"
                )
            )

            timeout_in(60)
            try:
                while True:
                    command = self.commands_queue.get()
                    while command[0].nickname != guesser.nickname:
                        if command[0].nickname == ".":
                            if command[1][0] == "-":
                                return
                        command = self.commands_queue.get()
                    letter = command[1].lower()
                    if len(letter) != 1 and len(letter) != len(self.word):
                        guesser.socket.send(
                            "Only guess letters or the entire word: ".encode("latin-1")
                        )
                        continue
                    break
            except TimeoutError:
                continue
            timeout_kill()

            last_guess = " "

            if len(letter) == 1:
                # Assign weighted scoring for each letter guess, and last guess string
                if letter in self.tried_letters:
                    self.fails += 1
                    last_guess = (
                        '\x1B[01;36mLAST GUESS\x1B[0m\n\x1B[01;36m"'
                        + letter.upper()
                        + '"\x1B[0m: \x1B[91mguessed already!\x1B[0m\n'
                    )
                    guesser.score -= 5 + (guesser.score // 10)
                elif letter not in self.word.lower():
                    self.fails += 1
                    last_guess = (
                        '\x1B[01;36mLAST GUESS\x1B[0m\n\x1B[01;36m"'
                        + letter.upper()
                        + '"\x1B[0m: \x1B[91mno!\x1B[0m\n'
                    )
                    guesser.score -= 12 + (guesser.score // 20)
                else:
                    last_guess = (
                        '\x1B[01;36mLAST GUESS\x1B[0m\n\x1B[01;36m"'
                        + letter.upper()
                        + '"\x1B[0m: \x1B[92myes!\x1B[0m\n'
                    )
                    guesser.score += 50 // max(1, guesser.score // 500)

                if letter not in self.tried_letters:
                    self.tried_letters.append(letter)

            else:
                # Scoring for entire word guesses
                if letter == self.word.lower():
                    guesser.score += 200
                    self.tried_letters += list(self.word.lower())
                else:
                    self.fails += 1
                    last_guess = (
                        '\x1B[01;36mLAST GUESS\x1B[0m\n\x1B[91m"'
                        + letter
                        + '"\x1B[0m\n'
                    )
                    guesser.score -= 200 + (guesser.score // 5)

            # Clear screen and print scores
            send_all(self.players, GRAPHICS["clear"])
            send_all(
                self.players,
                "\x1B[01;36mSCORE\x1B[0m\n" + str(self.players.scoreboard()) + "\n\n",
            )

            # Print the latest guessed letter or word, as string-fied above
            send_all(self.guessers, last_guess)

            self.update_stats(tried_letters=self.tried_letters, fails=self.fails)

            if self.fails == 10 or is_guessed(self.word, self.tried_letters):
                break
