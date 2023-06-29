"""ANSI graphics for overall TUI, server and client"""


def should_countdown(number):
    """Countdown values should be printed if here"""
    return number in [
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        10.0,
        30.0,
        60.0,
        90.0,
        120.0,
        180.0,
        300.0,
    ]


def string_to_masked(string, to_show):
    """Return the input string wrapped, colorized and masked. Use lowercase for list to_show."""
    out = ""
    for i, strchar in enumerate(string):
        if (i + 1) % 48 == 0:
            out += "-\n-"
        if strchar.lower() in to_show or not strchar.isalpha():
            out += "\x1B[01;36m" + strchar + "\x1B[0m"
        else:
            out += "."
    return out


GRAPHICS = {
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
