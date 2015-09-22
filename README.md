# pbjbt

IRC bot we're writing from scratch for fun.

## Resources

* [IRC RFC 1459](https://tools.ietf.org/html/rfc1459)
* [IRC RFC 2812](https://tools.ietf.org/html/rfc2812)
* [Wikipedia List of IRC commands](https://en.wikipedia.org/wiki/List_of_Internet_Relay_Chat_commands)
* [O'Reilly IRC bot example](http://archive.oreilly.com/pub/h/1968)
* [Poorly formatted internet resource](http://www.devshed.com/c/a/Python/Python-and-IRC/)

## Class Layout & Architecture

| Class | Description | Important Methods |
| ----- | ----------- | ----------------- |
| IRCConnection | handle all direct operations with socket & expose a higher-level interface the bot can interact with | recv_forever(), message(), join(), part() |
| IRCBot | handle all inbound message processing and user interaction | handle(), run() |

## Command Ideas

| Command | Action | Channel/Private/Both? |
| ------- | ------ | --------------------- |
| .join {channel} | Join a channel | Both |
| .log {channel} | Turn on logging for a channel | Both |

## Possible Pronunciations

* pubpuhjamabot
* pib-jibt
* peanut butter jelly bot
