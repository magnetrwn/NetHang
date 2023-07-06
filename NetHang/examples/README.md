# Sample games

---

## Hangman

### Basic game structure

*This is a sample game, which means your game can be structured differently as long as an interfacing class can be provided to the server.*

+ `hangman.py`: A simple game of hangman, this is also the default game loaded when no game is defined on creating a NetHangServer() object.
+ `hangman.json`: Graphics and configs for hangman, `clear` `title` `opening` must be present for the server to load them on users joining.

### Config options in `hangman.json`

*These settings can be changed for balancing games, while other options provide graphical data.*

+ `games`: Number of games (unused).
+ `rounds`: Number of rounds in one game.
+ `turns`: Number of turns in one round (unused).

---
