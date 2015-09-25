# pbjbt

IRC bot we're writing from scratch for fun.

## Resources

* [IRC RFC 1459](https://tools.ietf.org/html/rfc1459)
* [IRC RFC 2812](https://tools.ietf.org/html/rfc2812)
* [Wikipedia List of IRC commands](https://en.wikipedia.org/wiki/List_of_Internet_Relay_Chat_commands)
* [O'Reilly IRC bot example](http://archive.oreilly.com/pub/h/1968)
* [Poorly formatted internet resource](http://www.devshed.com/c/a/Python/Python-and-IRC/)
* [Python Decorators I](http://www.artima.com/weblogs/viewpost.jsp?thread=240808)
* [Python Decorators II](http://www.artima.com/weblogs/viewpost.jsp?thread=240845)

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

## Future Design Plans

Eventually, it'd be nice to have something where we could easily tack on command methods.
Something like "if you see a message starting with '.foo', perform method bar() with all subsequent words as arguments'
We can probably abstract this as a command registration system- keep a table of trigger regular expressions to callback methods
If so, possible method signature-
  .addCommand(cmd_regex, method_name, arg_handling)
    method_name is the name of callback method
    arg_handling is one of:
      pass -> give list of all subsequent tokens as an arg to the method (default)
      first -> give first token as arg, discard the rest
      groups -> if there are match groups in the regex, pass all of the groups as args to the method
      none -> discard everything, just call me please & thank you
With this argument handling scheme, we can easily write flexible methods that handle the token list.


We could even use decorators to call the callback method with code for checking the regex and parsing the arg handling scheme before calling it, to sort to the appropriate argument schemes

^ I ended up doing that

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
