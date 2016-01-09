# pbjbt

IRC bot I'm writing from scratch for fun.

`vim -S`

## Resources

* [IRC RFC 1459](https://tools.ietf.org/html/rfc1459)
* [IRC RFC 2812](https://tools.ietf.org/html/rfc2812)
* [Wikipedia List of IRC commands](https://en.wikipedia.org/wiki/List_of_Internet_Relay_Chat_commands)
* [O'Reilly IRC bot example](http://archive.oreilly.com/pub/h/1968)
* [Poorly formatted internet resource](http://www.devshed.com/c/a/Python/Python-and-IRC/)
* [Python Decorators I](http://www.artima.com/weblogs/viewpost.jsp?thread=240808)
* [Python Decorators II](http://www.artima.com/weblogs/viewpost.jsp?thread=240845)


## Adding a Command

Add a method inside of class IRCBot and decorate it like so:

```python
@addCommand('^\.match-me', 'pass'):
def match_me(self, msg_object, the_rest_of_the_tokens):
  self.conn.message(msg_object['dest'], 'Whoa! I got ' + str(the_rest_of_the_tokens))
```

Then, put that into IRCBot.handle() like the rest of them (TODO make that easier)

Now, whenever the bot sees a message in a channel or a private message staring with '.match-me', it'll pass the rest of the words off to the channel or user it came from.

```
delucks -> pbjbt: .match-me foo bar baz
pbjbt -> delucks: Whoa! I got ('foo', 'bar', 'baz')
```

This is a pretty easy pattern, as the second arg to the function gets auto-magically replaced with the split up tokens like you specified in the generator. You can make simpler commands with 'none', check out the source for `handle_version()`

### The Message "Object"

The message object that's passed off to those functions is actually a dict. It's built by the `split_msg()` method inside of `IRCBot`. Different fields are available depending on the type of message. All the following examples are generated from that function.

*Input string:* ":nick!username@hostname.net JOIN :#channel"
```json
{"nick": "nick", "host": "hostname.net", "raw_msg": "nick!~username@hostname.net JOIN :#channel", "type": "JOIN", "realname": "username"}
```

*Input string:* ":nick!username@hostname.net PRIVMSG #channel :message context"
```json
{
  "host": "hostname.net",
  "type": "PRIVMSG"
  "dest": "#channel",
  "nick": "nick",
  "realname": "username",
  "message": "message context",
  "raw_msg": "nick!~username@hostname.net PRIVMSG #channel :message context",
}
```

*Input string:* ":hostmask QUIT :Quit:WeeChat 0.4.2"
```json
{
  "host": "hostmask",
  "type": "QUIT"
  "raw_msg": "hostmask QUIT :Quit:WeeChat 0.4.2",
}
```

*Input string:* ":fqdn-of-server.com 002 nick :Your host is irc.foo.bar.edu, running version InspIRCd-2.0"
```json
{
  "host": "fqdn-of-server.com",
  "type": 2
  "raw_msg": "fqdn-of-server.com 002 nick :Your host is irc.foo.bar.edu, running version InspIRCd-2.0",
}
```

*Input string:* ":fqdn-of-server.com PING nick"
```json
{
  "host": "fqdn-of-server.com",
  "type": "PING"
  "raw_msg": "fqdn-of-server.com PING nick",
}
```

As you can see, all of them have the 'host' and 'type' fields. Usually the messages which are useful to us are type PRIVMSG, as they're coming to us from users in channels or private messages. More fields are added so you can properly respond to the user.

## Command Ideas

| Command | Action | Channel/Private/Both? |
| ------- | ------ | --------------------- |
| .join {channel} | Join a channel | Both |
| .log {channel} | Turn on logging for a channel | Both |
| .weather {zip code} | Curl some weather API for weather info | Both |
| {word}++/-- | Increment/decrement a counter for a username or word | Channel |
| s/{regex}/{regex}/ | Apply a regex to the last message a user sent | Both |
| .ping {hostname} | Ping, and display statistics, to host. (needs rate limiting) | Channel |
| .search {-engine google} {search term} | perform a search and send back the top n results | Private |
| .calculate {expr} | Calculate some simple arithmetic expression and return the results | Both |
| .history {query} | Grep log for the query string | Both, if logging is enabled |

Use markov-chain based keyword recognition to respond to direct mentions in channels.

## Possible Pronunciations

* pubpuhjamabot
* pib-jibt
* peanut butter jelly bot
