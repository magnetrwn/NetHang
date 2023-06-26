# NetHang

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/magnetrwn/NetHang/badge)](https://www.codefactor.io/repository/github/magnetrwn/NetHang)

Hangman client-server game package (and soon library for client-server multiplayer lobby games), written in Python using no external libraries for maximum compatibility. Clients can use any TCP socket application (e.g. nc) to connect and play!

## Asciinema Demo
<script async id="asciicast-593263" src="https://asciinema.org/a/593263.js"></script>

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
