# NetHang

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/magnetrwn/NetHang/badge)](https://www.codefactor.io/repository/github/magnetrwn/NetHang)
[![Coverage Status](https://coveralls.io/repos/github/magnetrwn/NetHang/badge?branch=main)](https://coveralls.io/github/magnetrwn/NetHang?branch=main)

**Note:** This was my Python project to get up to speed with the language and especially `setuptools`, `multiprocessing` and `socket`. It's development quality, not good as a library. Suggested use is only as educational material.

Compact server library to manage multiplayer lobbies for games, even as barebones as netcat clients, using only standard Python packages. There are sample implementations of games in the `NetHang/examples` folder, which can be useful to demonstrate what the library automates. The demo shows a sample implementation of a game of hangman, which is located in the examples folder.

Check out the `NetHang/examples` [README](NetHang/examples/README.md) and the `NetHang/config` [README](NetHang/config/README.md).

## WebM Demo (Large)

![WebM Demo](demo.gif)

## Installation

You have two options for installation:

+ **Download the Wheel**: Grab the pre-built wheel file (`NetHang-<version>-py3-none-any.whl`) from the latest release.
+ **Manual Installation**: Run `make install` from the command line to install the application yourself.

## Requirements

To use NetHang and generate the installation wheel, you need to have the following requirements installed:

+ `build`
+ `setuptools`

If you download the pre-built wheel, **you don't need to install** these setup libraries.

Additionally, the following requirements are set for developing NetHang, specifically for linting, formatting, and testing the package before merging pull requests:

+ Requirements are explicitly stated in the [requirements.txt](requirements.txt) file.
+ The project uses Trunk Check (VSCode extension) for consistent code checking across multiple developer platforms.

## Usage

Once installed, follow these steps to start the server:

+ Open a terminal or command prompt.
+ Run `NetHang` or `nethang` to start the server.

Make sure to check the configuration file `config/settings.json`, which is bundled with NetHang in Python's site-packages directory when installed. This file allows you to configure the server behavior when running from the shell or loading defaults for each run of NetHangServer.

You can also use the NetHang package as a module to further customize its usage, or have multiple servers at once. Here's an example:

```python
from NetHang.server import NetHangServer

server = NetHangServer("localhost")
server.run()

# Runs in background processes, not blocking

server.stop()
exit()
```

This usage will start the server with `examples/hangman.py` as the default game class to run (a sample multiplayer game of hangman using netcat), but this should be set to what you want your game class to be using the `game_class` parameter:

```python
server = NetHangServer("localhost", game_class=MyGame)
```

Your game class needs to have a `game_data` dict defined for graphics to be sent to users while joining. Please check `examples/hangman.py` implementation.

**Note:** At the moment, logging is not present and basic print statements are used instead. Logging support will be added soon.

## Contributing

Feel free to send your own suggestions or PRs if you want to help!

## License

This project is licensed under the [MIT License](LICENSE).
