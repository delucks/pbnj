import time
import inspect
import logging
from types import GeneratorType

from pbnj.connection import Connection
from pbnj.models import Message, Command, _builtin_command
from pbnj import __version__

log = logging.getLogger("pbnj")


class Bot:
    def __init__(
        self,
        nick,
        initial_channels=[],
        username=None,
        realname=None,
        use_builtin=True,
        builtin_prefix="^\.",
        connect_wait=0,
        follow_invite=True,
        ssl=False,
    ):
        self.nick = nick
        self.username = username or nick
        self.realname = realname or nick
        self.channels = initial_channels
        self.max_msg_len = 300
        self.commands = []
        self.conn = None
        self.use_builtin = use_builtin
        self.builtin_prefix = builtin_prefix
        self.connect_wait = connect_wait
        self.follow_invite = follow_invite
        self.ssl = ssl

    def __str__(self):
        return "pbnj.Bot {}".format(self.nick)

    def __repr__(self):
        return "pbnj.Bot {}, (user: {} real: {})".format(
            self.nick, self.username, self.realname
        )

    def _is_connected(self):
        return self.conn is not None

    def _channelify(self, text_stream):
        """ensure an iterable of channels start with #"""
        for ch_name in text_stream:
            if ch_name.startswith("#"):
                yield ch_name
            else:
                yield "#" + ch_name

    def _messageify(self, text_stream):
        """turn the raw text coming off the socket into a stream of objects"""
        for raw_message in text_stream:
            yield Message(raw_message)

    def _enable_builtin_commands(self):
        """check for _builtin_command decorated commands, insert them"""
        log.debug("Checking methods for builtin commands")
        for m_name, method in inspect.getmembers(self, inspect.ismethod):
            if "_command" in dir(method):
                log.debug("{} is a command!".format(m_name))
                self.commands.append(
                    Command(self.builtin_prefix + method._filterspec, method)
                )
        log.debug(str(self.commands))

    def connect(self, addr, port=6667):
        """create a connection to an address, or return one if it already exists"""
        if not self._is_connected():
            self.conn = Connection(addr, port, __version__, use_ssl=self.ssl)
        return self.conn

    def command(self, filterspec):
        """the decorator which marks an external function as a Command in the
        bot's context
        """

        def real_decorator(function):
            log.debug("Creating command for function {}".format(function))
            c = Command(filterspec, function)
            self.commands.append(c)
            log.debug("Added to self.commands")
            return function

        log.debug("Exiting command() decorator")
        return real_decorator

    def joinall(self, channels):
        """joins a bunch of channels"""
        success = True
        for channel in self._channelify(channels):
            self.channels.append(channel)
            success = success and self.conn.join(channel)
        return success

    def part(self, channels):
        """leaves a bunch of channels :( """
        for channel in self._channelify(channels):
            self.channels.remove(channel)
            self.conn.part(channel)

    def raw_send(self, message):
        """deliver a message directly to the connection- useful for doing things
        like MODE"""
        return self.conn.send(message)

    def run(self):
        """set up and connect the bot, start looping!"""
        invitation = "INVITE " + self.nick
        if self.use_builtin:
            self._enable_builtin_commands()
        # start the connection
        with self.conn:
            # make sure we're registered to the irc network
            self.conn.register(self.username, self.nick, self.conn.addr, self.realname)
            time.sleep(self.connect_wait)
            # handle any channels the user asked us to join
            if self.channels:
                log.info("Joining initial channels")
                for channel in self.channels:
                    self.conn.join(channel)
            for msg in self._messageify(self.conn.recieve()):
                if self.follow_invite and invitation in msg.raw_msg:
                    destination = msg.raw_msg.split(":")[-1]
                    self.joinall([destination])
                self.handle(msg)

    def handle(self, message):
        """Iterates through the registered commands and attempts to find a
        command which matches the incoming Message. Does this by calling
        command.match() for each.
        """
        for command in self.commands:
            log.debug("Checking command {}".format(command.name))
            if command.match(message):  # the call
                log.info("{} matched!".format(command.name))
                resp = command(message)
                log.info("Called command method {0}".format(command.name))
                if resp:
                    log.info("Got a reply: {}".format(resp))
                    # we have something to hand back
                    if type(resp) == str:
                        log.debug("Response is a string, sending...")
                        return self.conn.message(message.reply_dest, resp)
                    elif isinstance(resp, GeneratorType):
                        log.debug("Response is a generator, giving back the contents")
                        success = True
                        for reply in resp:
                            success = success and self.conn.message(
                                message.reply_dest, reply
                            )
                        return success
                    elif isinstance(resp, bool):
                        log.debug("The function handed back a boolean, returning it")
                        return resp
                    else:
                        log.warning(
                            "Got back a weird type from command {}".format(command.name)
                        )
                        log.warning(resp)
                        return False
                break  # don't check any more methods
            else:
                log.debug("{0} failed to match {1}".format(command.name, message))
        log.debug("No matches found.")
        return False  # couldn't find a match for the command at all

    @_builtin_command("version")
    def version(self, message):
        """display the library version"""
        return "{}: {} version {}".format(message.nick, self.nick, __version__)

    @_builtin_command("ping")
    def ping(self, message):
        """pong"""
        return "{}: pong".format(message.nick)

    @_builtin_command("join")
    def join(self, message):
        """join a number of channels"""
        if len(message.args) < 1:
            return "Usage: {}join #channelname".format(self.builtin_prefix)
        else:
            log.debug("We got channels: {}".format(message.args))
            return self.joinall(message.args)

    @_builtin_command("help")
    def help(self, message):
        """return name and description of all commands"""
        if len(message.args) == 2:
            # we want detailed help for a specific command
            for command in self.commands:
                if command.name == message.args[1]:
                    return "{}: {} - {}".format(
                        message.nick, command.name, str(command)
                    )
        else:
            return "Available commands: " + " ".join(c.name for c in self.commands)
