Certainly! Here's an improved version of your README.md file for your Python client-server application:

# NetHang

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/magnetrwn/NetHang/badge)](https://www.codefactor.io/repository/github/magnetrwn/NetHang)

NetHang is a compact client-server Python application that allows you to play hangman online by starting a server and allowing clients to connect using netcat (nc) or any other TCP client.

### Asciinema Demo

## Installation

You have two options for installation:

1. **Download the Wheel**: Grab the pre-built wheel file (`NetHang-<version>-py3-none-any.whl`) from the `dist` directory.
2. **Manual Installation**: Run `make install` from the command line to install the application yourself.

## Usage

Once installed, follow these steps to start the server:

1. Open a terminal or command prompt.
2. Run `NetHang` or `nethang` to start the server.

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

## Contributing

Feel free to send your own suggestions or even PRs if you want to help!

## License

This project is licensed under the [MIT License](LICENSE).