'''. HANGMAN NETCAT GAME SERVER:
| This file is a compact, client-server Python application to play
| hangman using netcat (nc), written for linux systems.
| ... TODO extend module docstring ...
'
'''

# client terminal min width: 48 chars

#######################################
#                                     #
#        Setup globals/imports        #
#                                     #
#######################################

from multiprocessing import Process, SimpleQueue, cpu_count
#from _ctypes import PyObj_FromPtr as di
from select import select
from time import sleep
import socket as so
import sys

global_paragraphs = {
  'clear':
'\033[2J\033[H',

  'title':
'\033[2J\033[H\x1B[01;36m ============= Welcome to Hangman =============\x1B[0m  \n',

  'opening':
'''\nWelcome to the game of Hangman on command line!
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
You can \x1B[01;36mquit\x1B[0m at any moment with \x1B[01;36m^C\x1B[0m (Ctrl-C).\n\n''',

  'hangman0':
'''






         [ 0/9     ]
''',

  'hangman1':
'''

|
|
|
|
|
|        [\x1B[07;36m \x1B[0m1/9     ]
''',

  'hangman2':
'''
 ____
/
|
|
|
|
|
|        [\x1B[07;36m 2\x1B[0m/9     ]
''',

  'hangman3':
'''
 ____
/   |
|
|
|
|
|
|        [\x1B[07;36m 3/\x1B[0m9     ]
''',

  'hangman4':
'''
 ____
/   |
|  ( )
|
|
|
|
|        [\x1B[07;36m 4/9\x1B[0m     ]
''',

  'hangman5':
'''
 ____
/   |
|  ( )
|   |
|   |
|   |
|
|        [\x1B[07;36m 5/9 \x1B[0m    ]
''',

  'hangman6':
'''
 ____
/   |
|  ( )
|  /|
| / |
|   |
|
|        [\x1B[07;36m 6/9  \x1B[0m   ]
''',

  'hangman7':
'''
 ____
/   |
|  ( )
|  /|\\
| / | \\
|   |
|
|        [\x1B[07;36m 7/9   \x1B[0m  ]
''',

  'hangman8':
'''
 ____
/   |
|  ( )
|  /|\\
| / | \\
|   |
|  /
| /      [\x1B[07;36m 8/9    \x1B[0m ]
''',

  'hangman9':
'''
 ____
/   |
|  ( )
|  /|\\
| / | \\
|   |
|  / \\
| /   \\  [\x1B[07;36m 9/9     \x1B[0m]
'''
}

def string_to_masked(string, to_show):
  '''Return the input string wrapped, colorized and masked.'''
  out = ''
  for i in range(len(string)):
    if i%48 == 0:
      out += '\n'
    if string[i] in to_show or not string[i].isalpha():
      out += '\x1B[01;36m'+string[i]+'\x1B[0m'
    else:
      out += '.'
  return out


#########################################
#                                       #
#        PlayerList: all classes        #
#                                       #
#########################################

class PlayerList():
  '''List of all players, using the Player class.'''

  def __init__(self):
    self.player_list = []

  def is_player_n(self, nickname):
    '''Check if there is a player with a certain nickname.'''
    for player in self.player_list:
      if player.nickname == nickname:
        return True
    return False

  def is_player_s(self, socket):
    '''Check if there is a player with a certain socket.'''
    for player in self.player_list:
      if player.socket == socket:
        return True
    return False

  def get_player_n(self, nickname):
    '''Get a player by nickname.'''
    for player in self.player_list:
      if player.nickname == nickname:
        return player
    return None

  def get_player_s(self, socket):
    '''Get a player by socket.'''
    for player in self.player_list:
      if player.socket == socket:
        return player
    return None

  def get_sockets(self):
    '''Get a list of all player sockets.'''
    return [player.socket for player in self.player_list]

  def get_nicknames(self):
    '''Get a list of all player nicknames.'''
    return [player.nickname for player in self.player_list]

  def add_player(self, player):
    '''Add a player of Player type.'''
    self.player_list.append(player)

  def drop_player_n(self, nickname):
    '''Drop a player by nickname.'''
    i = 0
    for player in self.player_list:
      if player.nickname == nickname:
        del self.player_list[i]
        break
      i += 1

  def drop_player_s(self, socket):
    '''Drop a player by socket.'''
    i = 0
    for player in self.player_list:
      if player.socket == socket:
        del self.player_list[i]
        break
      i += 1

class Player():
  '''Each Player combines a socket and a nickname.'''

  def __init__(self, socket, nickname):
    self.socket = socket
    self.nickname = nickname


############################################
#                                          #
#        HangmanServer: all classes        #
#                                          #
############################################

class HangmanServer():
  '''Contains all methods to run the game server for hangman.'''

  def __init__(self, server_address, server_socket=so.socket(so.AF_INET, so.SOCK_STREAM), max_conn=20):
    port_ok = False
    bind_tries = 0
    while not port_ok and bind_tries < 10:
      try:
        port = 55550+bind_tries
        bind_tries += 1
        server_socket.bind((server_address, port))
      except (PermissionError, OSError) as e:
        print('\x1B[31m'+e.args[1]+'\x1B[0m')
      else:
        port_ok = True
    if port_ok is False:
      sys.exit('\x1B[31mCould not bind to socket!\x1B[0m')
    server_socket.listen(max_conn)
    print('Server on '+server_address+':'+str(port))

    self.server_socket = server_socket
    self.players = PlayerList()

  def accept_clients_worker(self, server_socket, players_read_queue, players_write_queue):
    '''Worker daemon process that accepts new client connections.'''
    while True:
      try:
        client_raw = server_socket.accept()
        sleep(0.5)
        client_raw[0].send(global_paragraphs['title'].encode('utf-8'))
        worker_players = players_read_queue.get()
        ## UNCOMMENT FOR DUPLICATE IP REJECTION
        #if worker_players.is_player_s(client_raw[0]):
        #  client_raw[0].send('This client IP is already in use!\n'.encode('utf-8'))
        #  client_raw[0].close()
        #else:
        client_nickname = '?'
        while not client_nickname.isalnum() or len(client_nickname) < 2:
          sleep(0.5)
          client_raw[0].send('Nickname (alphanumeric, 2-32 chars): '.encode('utf-8'))
          try:
            client_nickname = client_raw[0].recv(33)[:-1].decode('utf-8')
            if worker_players.is_player_n(client_nickname):
              client_raw[0].send('This nickname is already in use!\n'.encode('utf-8'))
              client_nickname = '?'
          except UnicodeDecodeError:
            client_nickname = '?'
        players_write_queue.put(Player(client_raw[0], client_nickname))
        client_raw[0].send(global_paragraphs['opening'].encode('utf-8'))
        print('\x1B[36m'+client_nickname+' joined\x1B[0m')
      except BrokenPipeError:
        sleep(0.5)
      except KeyboardInterrupt:
        return

  def run(self):
    '''Run the hangman server.'''
    players_read_queue = SimpleQueue()
    players_write_queue = SimpleQueue()

    for _ in range(max(1, min(4, cpu_count()-1))):
      Process(target=HangmanServer.accept_clients_worker,
              args=(self, self.server_socket,
                    players_read_queue,
                    players_write_queue),
              daemon=True).start()

    while True:
      while not players_write_queue.empty():
        self.players.add_player(players_write_queue.get())
      while not players_read_queue.empty():
        players_read_queue.get()
      for _ in range(max(1, min(4, cpu_count()-1))):
        players_read_queue.put(self.players)

      try:
        ready_sockets = select(self.players.get_sockets(), [], [], 2)[0]
      except KeyboardInterrupt:
        self.server_socket.close()
        sys.exit('\r\x1B[90mKeyboardInterrupt\x1B[0m')

      for socket in ready_sockets:
        player = self.players.get_player_s(socket)
        try:
          data = socket.recv(256)
          if not data:
            print('\x1B[36m'+player.nickname+' left\x1B[0m')
            socket.close()
            self.players.drop_player_n(player.nickname)
          else:
            try:
              decoded_data = data[:-1].decode('utf-8')
            except UnicodeDecodeError:
              continue
            # send tuple of (remote_ip, decoded data) to a queue read by
            # a game loop process here...

            print('\x1B[90m<'+player.nickname+'>:\x1B[0m '+decoded_data)
        except ConnectionResetError:
          print('\x1B[33m'+player.nickname+' reset connection\x1B[0m')
          socket.close()
          self.players.drop_player_n(player.nickname)

    #self.server_socket.close()


##########################################
#                                        #
#        HangmanGame: all classes        #
#                                        #
##########################################

class HangmanGame():
  '''Base class for all turn-based hangman games.'''

class RoundRobinGame(HangmanGame):
  '''Round-robin hangman gamemode.'''

class KingHillGame(HangmanGame):
  '''King of the hill hangman gamemode.'''

class WordlistGame(HangmanGame):
  '''Wordlist hangman gamemode.'''

class Round():
  '''A single round of the turn-based hangman game.'''

class Turn():
  '''A single turn of the turn-based hangman game.'''

class TimeAttackGame():
  '''Time attack hangman gamemode, not turn-based.'''

class TimeAttackRound():
  '''A single round of the time attack version hangman game.'''


##########################
#                        #
#        __main__        #
#                        #
##########################

if __name__ == '__main__':
  if len(sys.argv) == 1:
    try:
      host = input('Type server IP: ')
      HangmanServer(host).run()
    except KeyboardInterrupt:
      sys.exit()
  elif len(sys.argv) == 2:
    host = sys.argv[1]
  else:
    sys.exit('\x1B[31mToo many arguments!\x1B[0m')
