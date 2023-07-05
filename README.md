# NetHang

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/magnetrwn/NetHang/badge)](https://www.codefactor.io/repository/github/magnetrwn/NetHang)

Compact server library to manage multiplayer lobbies for most games, even as barebones as netcat clients. There are sample implementations of games in the `NetHang/examples` folder, which can be useful to demonstrate what the library automates. This README will be extended with recent updates soon.
Also check out the `NetHang/examples` README and the `NetHang/config` README.

**Warning! Outdated information (from dev18) ahead!**

---

## Asciinema Demo

[![asciicast](https://asciinema.org/a/593263.svg)](https://asciinema.org/a/593263)

## Installation

You have two options for installation:

+ **Download the Wheel**: Grab the pre-built wheel file (`NetHang-<version>-py3-none-any.whl`) from the latest release.
+ **Manual Installation**: Run `make install` from the command line to install the application yourself.

## Usage

Once installed, follow these steps to start the server:

+ Open a terminal or command prompt.
+ Run `NetHang` or `nethang` to start the server.

Make sure to check the configuration file `config/settings.yml`, which is bundled with NetHang in Python's site-packages directory when installed. This file allows you to configure the server behavior when running from the shell or loading defaults for each run of HangmanServer.

You can also use the NetHang package as a module to further customize its usage, or have multiple servers at once. Here's an example:

```python
from NetHang.server import HangmanServer

server = HangmanServer("localhost")
server.run()

# Do something else

server.stop()
exit()
```

**Note:** At the moment, logging is not present and basic print statements are used instead. Logging support will be added soon.

## Future

The project goal extends beyond hangman (despite the repo name). The plan is to transform the application into a versatile library for CLI games. Future updates (post-0.0.x) will focus on transforming the project into a general-purpose library model, to provide client-server functionality. This enhances project flexibility and enables developers to focus on their game.

## Contributing

Feel free to send your own suggestions or PRs if you want to help!

## License

This project is licensed under the [MIT License](LICENSE).
