"""Fundamental classes and functions to manage players"""


from random import randint


def generate_rejoin_code():
    """Generates a four number code, possibly with leading zeros."""
    return str(randint(0, 9999)).zfill(4)


class Player:
    """Each Player combines a socket and a nickname, and can have an address or rejoin code."""

    def __init__(self, socket, nickname, address=None, rejoin_code=None):
        self.socket = socket
        self.nickname = nickname
        self.address = address
        if rejoin_code is None:
            self.rejoin_code = generate_rejoin_code()
        else:
            self.rejoin_code = rejoin_code


class PlayerList:
    """List of all players, using the Player class."""

    def __init__(self):
        self.player_list = []

    def is_player(self, nickname=None, socket=None, address=None):
        """Check if there is a player with a certain nickname, socket or address."""
        if nickname is not None:
            for player in self.player_list:
                if player.nickname == nickname:
                    return True
        if socket is not None:
            for player in self.player_list:
                if player.socket == socket:
                    return True
        if address is not None:
            for player in self.player_list:
                if player.address == address:
                    return True
        return False

    def get_player(self, nickname=None, socket=None):
        """Get a player by nickname or socket."""
        if nickname is not None:
            for player in self.player_list:
                if player.nickname == nickname:
                    return player
        if socket is not None:
            for player in self.player_list:
                if player.socket == socket:
                    return player
        return None

    def get_sockets(self):
        """Get a list of all player sockets."""
        return [player.socket for player in self.player_list]

    def get_nicknames(self):
        """Get a list of all player nicknames."""
        return [player.nickname for player in self.player_list]

    def add_player(self, player):
        """Add a player of Player type."""
        self.player_list.append(player)

    def drop_player(self, nickname=None, socket=None):
        """Drop a player by nickname or socket."""
        if nickname is not None:
            for i, player in enumerate(self.player_list):
                if player.nickname == nickname:
                    del self.player_list[i]
                    break
        if socket is not None:
            for i, player in enumerate(self.player_list):
                if player.socket == socket:
                    del self.player_list[i]
                    break
