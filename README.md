# pbjbt

pbjbt is an IRC bot micro-framework. It's designed so you can write an absolute minimum of boilerplate to have a fully working and extensible bot.

pbjbt is:
- Tested (heading toward 100% coverage)
- Small (>500sloc without tests)
- Portable (only requires the standard library)

## Demo!

`weather.py`

```python
from pbjbt import Bot
bot = Bot('forecaster')

@bot.command('^\.weather')  # regular expression or callable accepted
def weather(message):
    '''get the weather for a zip code in the US'''
    # the commands' __doc__ are used in the bot's built-in ".help" command
    zip_code = message.args[0]
    response = requests.get('http://my.weather.com/api/{0}'.format(zip_code))
    # will be sent back to the source channel by default
    return '{0}: Currently {r.temp} degrees F'.format(message.nick, r=response.json())

if __name__ == '__main__':
    bot.connect('irc.network.com')
    bot.run()
```

The method you decorate with `@bot.command(...)` will reply to the channel that created the message if you return:
- strings
- a Generator via yield (all yielded strings will be sent to the channel)

If you return a prepared pbjbt.Reply object, it will execute that. (Prepared replies are TODO)

## Requirements

None! Using pbjbt is easy because we only use the standard library.

`(unless you want to run tests)`

In which case, you need `pytest` and `pytest-cov`. There's a requirements.txt too!

## Message objects

pbjbt hands you a Message object as the only argument to your command functions. This is a message from an IRC channel
or server the bot is a part of, and has a number of fields filled out that you can work with.

Normal fields:
- `raw_msg`: Message as recieved off the socket
- `host`: Hostname the message came from
- `type`: IRC command the message represents. If this is PRIVMSG or ACTION, additional fields are parsed.

PRIVMSG/ACTION fields:
- `dest`: channel the message came from
- `nick`: nick of the user the message came from
- `realname`: realname of the user the message came from
- `message`: trimmed message from the channel
- `args`: array of everything but the first word in "message"

## Hacking

`vim -S`

### Running the Tests

```shell
virtualenv -p $(which python3) .
source bin/activate
pip install -r requirements.txt
py.test
```

### TODOs

- Prepared Reply objects
- Chat history functionality, and response generation with basic ML

#### Built-in commands

| Command | Action | Channel/Private/Both? |
| ------- | ------ | --------------------- |
| .join {channel} | Join a channel | Both |
| .log {channel} | Turn on logging for a channel | Both |
| .calculate {expr} | Calculate some simple arithmetic expression and return the results | Both |
| .history {query} | Grep log for the query string | Both, if logging is enabled |

#### Extra commands (example?):

| Command | Action | Channel/Private/Both? |
| ------- | ------ | --------------------- |
| .weather {zip code} | Curl some weather API for weather info | Both |
| {word}++/-- | Increment/decrement a counter for a username or word | Channel |
| s/{regex}/{regex}/ | Apply a regex to the last message a user sent | Both |
| .ping {hostname} | Ping, and display statistics, to host. (needs rate limiting) | Channel |
| .search {-engine google} {search term} | perform a search and send back the top n results | Private |

## Name?

Yeah I know it's weird. Initially I just called this "bot", but as it grew it
requried a name, so I called it "peanut-butter-jelly bot" as it should be as easy
to create an IRC bot with this library as it is to create a PB&J sammich.
Inspired by the terseness of the IRC protocol, I shortened it to "pbjbt".
