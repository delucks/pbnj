# pbnj

[![Build Status](https://travis-ci.org/delucks/pbnj.svg?branch=master)](https://travis-ci.org/delucks/pbnj)

pbnj is an python IRC bot library and framework. It's designed so you can write an absolute minimum of boilerplate to have a fully working and extensible bot.

pbnj is:
- Tested (near complete code coverage)
- Small (less than 500 lines of code without tests)
- Portable (built with the standard library)

## Installing

`pip install pbnj`

## Demo!

`weather.py`

```python
from pbnj.bot import Bot
bot = Bot('forecaster')

@bot.command('^\.weather [0-9]{5}')
def weather(message):
    '''get the weather for a zip code in the US'''
    zip_code = message.args[0]
    response = requests.get('http://my.weather.com/api/{0}'.format(zip_code))
    return '{0}: Currently {r.temp} degrees F'.format(message.nick, r=response.json())

if __name__ == '__main__':
    bot.connect('irc.network.com')
    bot.join('#channel')
    bot.run()
```

Channel log:
```none
> forecaster joins #channel
idler:          .weather 32490
forecaster:     idler: Currently 83 degrees F
idler:          .help
forecaster:     idler: weather - get the weather for a zip code in the US
```

(More examples can be found in the examples/ directory of this repository)

Argument to `@bot.command(...)` can be either a string or a callable that returns a boolean.

If it's a string, the string will be treated as a regular expression on all incoming PRIVMSG messages (anything in a channel or private message). If the regex matches, the command function will execute.

If it's a callable, it will be called with the Message object (see below) of each incoming message. If it returns true, the command function will execute.

The function you decorate with `@bot.command(...)` will reply to the channel that created the message if you return:
- strings
- a Generator via yield (all yielded strings will be sent to the channel)

If you decide to use builitn commands (for more info see below), help output will be populated automatically. The docstring of your function is the help message, with the name of the function used as the command's name.

Importantly, `pbnj` logs onto a logger named `pbnj`. If you want to see debugging & connection-related logs, give it some love.

## Requirements

None! Using pbnj is easy because we only use the standard library. If you find any code that isn't compatible on your platform, please issue a bug report.

If you want to run tests, you need `pytest` and `pytest-cov`. There's a requirements.txt for that too!

## Message objects

pbnj hands you a Message object as the only argument to your command functions. This is a message from an IRC channel or server the bot is a part of, and has a number of fields filled out that you can work with.

Normal fields:
- `raw_msg`: Message as recieved off the socket
- `host`: Hostname the message came from
- `type`: IRC command the message represents. If this is PRIVMSG or ACTION, additional fields are parsed.

`PRIVMSG`/`ACTION` fields:
- `dest`: channel the message came from
- `nick`: nick of the user the message came from
- `realname`: realname of the user the message came from
- `message`: trimmed message from the channel
- `args`: array of everything but the first word in "message"

## Built-in commands

`pbnj` ships with a number of commands that most botmakers build standard into their bots, usable by setting the `use_builtin` parameter of the `pbnj.Bot` constructor to true. You can change the prefix for these commands by setting the 'builtin_prefix' parameter in the Bot constructor. The default is  `^\.`

| Command | Action | Channel/Private/Both? |
| ------- | ------ | --------------------- |
| .join {channel} | Join a channel | Both |
| .version | Display the library version | Both |
| .ping | Send back "pong" | Both |
| .help | Show all commands this bot has, with help output of their `__doc__` | Both |

## Hacking

I'm a `vim` user, if you are too: `vim -S etc/Session.vim`

If you want to implement something interesting, send a PR! The source code is formatted using [black](https://github.com/ambv/black), please use it to format your patches.

### Running the Tests

Code coverage by loc is about 100%, but use case coverage is nowhere near that number. We welcome new bug reports, if you encounter behavior you don't expect please let me know!

```shell
virtualenv -p $(which python3) .
source bin/activate
pip install -r requirements.txt
py.test
```

### TODOs

- Prepared Reply objects
- Chat history functionality, and response generation with basic ML
- Make the help output behavior overrideable
- Exposing a logger to users

#### Command Ideas

| Command | Action | Channel/Private/Both? |
| ------- | ------ | --------------------- |
| .log {channel} | Turn on logging for a channel | Both |
| .calculate {expr} | Calculate some simple arithmetic expression and return the results | Both |
| .history {query} | Grep log for the query string | Both, if logging is enabled |
| .weather {zip code} | Curl some weather API for weather info | Both |
| {word}++/-- | Increment/decrement a counter for a username or word | Channel |
| s/{regex}/{regex}/ | Apply a regex to the last message a user sent | Both |
| .ping {hostname} | Ping, and display statistics, to host. (needs rate limiting) | Channel |
| .search {-engine google} {search term} | perform a search and send back the top n results | Private |

## License

pbnj is Copyright (c) 2016, James Luck. It is licensed under the GNU GPLv3. There is a copy of the license included in LICENSE.txt, peruse it there or at https://www.gnu.org/licenses/gpl-3.0.txt
