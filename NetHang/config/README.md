# Package configuration: `settings.json`

## `run.py`

*Settings for how the CLI behaves, when running the `nethang` command from shell.*

+ `game_class`: When working from CLI, this will import the requested package->module->class to run the NetHangServer game on. Initial value is the hangman sample game.
+ `always_at`: If not null, always use specified host address without asking the user.

## `server.py`

*Server configuration.*

+ `max_conn`: Maximum number of concurrent users.
+ `avail_ports`: Available ports to use, will only attach to one, `true` for random ports.
+ `new_conn_processes`: Number of new user handlers, for concurrent user connection.
+ `delay_factor`: Multiply all sleep() delays by this value.
+ `allow_same_source_ip`: Allow two or more users from the same source IP address.
+ `blacklisted`: Blacklist of IP addresses on server startup.
+ `lobby_time`: Duration of the pause between games, the value at which countdown starts.
