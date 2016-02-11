Samples of strings coming in we may see
* :nick!username@hostname.net JOIN :#channel
* :nick!username@hostname.net PRIVMSG #channel :message context
* :hostmask QUIT :Quit:WeeChat 0.4.2
* :fqdn.net 002 nick :Your host is irc.fqdn.net, running FooIRCd-0.1

Ideas and TODO:
* Multiple IRCConnections per bot, maybe each threaded
* Logging support for each channel, configurable on/off and only certain nicks or actions. Maybe in JSON
* Have some kind of a watchlist of words that just alert, maybe send some kind of a message (email, sms) on keywords
* Change the second argument of the command decorator to default to "groups"
*   You could also have a fairly sane default of "all of your groups get passed off if the regex matches"
* I think the idea of providing a method name instead of a regex is also good.
*   If the type of the first argument is 'str', make it a regex? If it's callable, call it?
* Wrap the '.' in front of commands into its own thing, apply commands as after that.
* You can also make it so messaging the bot directly 'bot: ping' works the same way as .ping
* @bot.command could work differently than @bot.environmental which would be for things like 'foo++' said without reference to the bot or a particular command word

Making a many/many relationship
-------------------------------

ok, how are we going to handle having multiple Connections per Bot
We could have each Connection be some kind of independent object that each
Bot subscribes to
Then, each message could be passed from the Connection level as not just a stream of text, but an object with a context
    Like "message" + "from network named "irc.foo.bar.edu"
Each bot will recieve the messsage at the same time, and potentially handle it differently depending on the type of network
Then, we could have a map of connections and bots, each sending data bidirectionally
    Each connection operates independently, and will log incoming messages as well as automagically respond to PINGs
    The idea is we could have connections running and logging without any bots active, and then activating a bot
    would be as simple as instantiating the class with references to the subscribing streams of each Connection
    We could have bots instantiate more Connections on their own, perhaps at the behest of the "user"

If this is the case, should message parsing logic occur in the Connection object, or later on in the processing pipeline?
    If we want this to scale beyond a single machine, we should consider separating out all these phases and having them linked in the network layer
    But that's so far away...

If the processing occurs in the Connection objects-
    We could log greater amounts of easily searchable metadata about each message
    Connection objects will have to be super optimized so we can correctly instantiate them
    Connection objects have to be their own threads
    Connection objects will have to have their own failure recovery (when the network gets chopped)
    Connection objects might feed into some kind of a message queue (pubsub)

Connection objects need to be instantiated by a Bot instance, because they have to give some kind of registration message containing Bot-level metadata when joining
How about this- instead of creating a Connection and then instantiating a Bot with it, we create the Bot first and it can create its own connections
    Each bot would need its own connection-handling logic

I think for right now, it's okay to go 1 bot -> many connections.

Later on we can focus on splitting that out to be a many/many relationship
