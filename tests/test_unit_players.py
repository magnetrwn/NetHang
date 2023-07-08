"""Tests for the players.py module."""

import socket as so

# TODO: because of possible future type hinting, do not use strings for testing sockets!

import NetHang


def test_rejoin_code():
    """Does the rejoin code gen return 4 digit codes?"""
    code = NetHang.players.generate_rejoin_code()
    assert len(code) == 4
    assert code.isdigit()


def test_player_initialization():
    """Create a test Player instance."""
    socket = so.socket()
    nickname = "TestNickname"
    address = "0.0.0.0"
    rejoin_code = "1234"
    score = 100

    player = NetHang.players.Player(socket, nickname, address, rejoin_code, score)
    assert player.socket == socket
    assert player.nickname == nickname
    assert player.address == address
    assert player.rejoin_code == rejoin_code
    assert player.score == score


def test_player_default_rejoin_code():
    """Create a test Player instance without providing a rejoin_code."""
    socket = so.socket()
    nickname = "TestNickname"

    player = NetHang.players.Player(socket, nickname)
    assert player.rejoin_code is not None


def test_player_default_score():
    """Create a test Player instance without providing a score."""
    socket = so.socket()
    nickname = "TestNickname"

    player = NetHang.players.Player(socket, nickname)
    assert player.score == 0


def test_player_list_initialization():
    """Assert that the player list is empty initially."""
    player_list = NetHang.players.PlayerList()
    assert player_list.count() == 0


def test_player_list_add_player():
    """Assert that the player list count increases after adding a player."""
    player_list = NetHang.players.PlayerList()
    player = NetHang.players.Player("TestSocket", "TestNickname")

    player_list.add_player(player)
    assert player_list.count() == 1


def test_player_list_drop_player():
    """Assert that the player with nickname "Nickname2" is dropped."""
    player_list = NetHang.players.PlayerList()
    player1 = NetHang.players.Player("Socket1", "Nickname1")
    player2 = NetHang.players.Player("Socket2", "Nickname2")
    player3 = NetHang.players.Player("Socket3", "Nickname3")

    player_list.add_player(player1)
    player_list.add_player(player2)
    player_list.add_player(player3)

    player_list.drop_player(nickname="Nickname2")
    assert player_list.count() == 2
    assert not player_list.is_player(nickname="Nickname2")


def test_player_list_get_player():
    """Assert that the correct players are retrieved."""
    player_list = NetHang.players.PlayerList()
    player1 = NetHang.players.Player("Socket1", "Nickname1")
    player2 = NetHang.players.Player("Socket2", "Nickname2")
    player3 = NetHang.players.Player("Socket3", "Nickname3")

    player_list.add_player(player1)
    player_list.add_player(player2)
    player_list.add_player(player3)

    retrieved_player1 = player_list.get_player(nickname="Nickname1")
    retrieved_player2 = player_list.get_player(socket="Socket3")
    assert retrieved_player1 == player1
    assert retrieved_player2 == player3


def test_player_list_scoreboard():
    """Assert the scores in the scoreboard dictionary."""
    player_list = NetHang.players.PlayerList()
    player1 = NetHang.players.Player("Socket1", "Nickname1", score=100)
    player2 = NetHang.players.Player("Socket2", "Nickname2", score=200)
    player3 = NetHang.players.Player("Socket3", "Nickname3", score=300)

    player_list.add_player(player1)
    player_list.add_player(player2)
    player_list.add_player(player3)

    scoreboard = player_list.scoreboard()
    assert scoreboard == {"Nickname1": 100, "Nickname2": 200, "Nickname3": 300}
