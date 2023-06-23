# NetHang

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/magnetrwn/NetHang/badge)](https://www.codefactor.io/repository/github/magnetrwn/NetHang)

NetHang is a compact client-server Python game that allows you to play hangman online by starting a server and allowing clients to connect using netcat (nc) or any other TCP client.

### Asciinema Demo

## Installation

You have two options for installation:

+ **Download the Wheel**: Grab the pre-built wheel file (`NetHang-<version>-py3-none-any.whl`) from the `dist` directory.
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

The project goal extends beyond hangman (despite the repo name). The plan is to transform the application into a versatile library that can support a wide range of turn-based online games (still CLI). Future updates will focus on transitioning to a general-purpose library model, extending the existing client-server functionality in the `NetHang/game.py` file. This approach enhances flexibility and enables developers to focus on their game.

## Contributing

Feel free to send your own suggestions or PRs if you want to help!

## License

This project is licensed under the [MIT License](LICENSE).
