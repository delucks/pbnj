from types import GeneratorType
import inspect
import logging
from pbjbt.connection import Connection
from pbjbt.models import Message, Command, _builtin_command
log = logging.getLogger()

VERSION='0.0.7'

class Bot:
    def __init__(self, nick, username=None, realname=None):
        self.nick = nick
        self.username = username or nick
        self.realname = realname or nick
        self.channels = []
        self.max_msg_len = 300
        self.commands = []
        self.conn = None

    def _parse_args(self, override=False):
        '''TODO: use argparse to give this Bot additional options from the CLI
        should be called when __name__ == __main__'''
        pass

    def _is_connected(self):
        return self.conn is not None

    def _channelify(self, text_stream):
        '''ensure an iterable of channels start with #'''
        for ch_name in text_stream:
            if ch_name.startswith('#'):
                yield ch_name
            else:
                yield '#' + ch_name

    def _messageify(self, text_stream):
        '''turn the raw text coming off the socket into a stream of objects'''
        for raw_message in text_stream:
            yield Message(raw_message)

    def connect(self, addr, port=6667):
        self.conn = Connection(addr, port, VERSION)
        return self.conn

    def command(self, filterspec):
        def real_decorator(function):
            c = Command(filterspec, function)
            self.commands.append(c)
            def wrapper(*args):
                return function(*args)
            return wrapper
        return real_decorator

    def join(self, channels):
        '''joins a bunch of channels'''
        for channel in self._channelify(channels):
            self.channels.append(channel)
            self.conn.join(channel)

    def part(self, channels):
        '''leaves a bunch of channels :( '''
        for channel in self._channelify(channels):
            self.channels.remove(channel)
            self.conn.part(channel)

    def run(self):
        '''set up and connect the bot, start looping!'''
        # check for _builtin_command decorated commands, insert them
        for m_name, method in inspect.getmembers(self, inspect.ismethod):
            log.debug('Checking if method {} is a builtin...'.format(m_name))
            if '_command' in dir(method):
                log.debug('{} is a command!'.format(m_name))
                #self.commands.insert(0, Command(method._filterspec, method))
                self.commands.append(Command(method._filterspec, method))
            else:
                log.debug('{} was not a command'.format(m_name))
        # start the connection
        with self.conn:
            # make sure we're registered to the irc network
            self.conn.register(self.username, self.nick, self.conn.addr, self.realname)
            # handle any channels the user asked us to join
            if self.channels:
                for channel in self.channels:
                    self.conn.join(channel)
            for msg in self._messageify(self.conn.recieve()):
                log.debug('Calling handle() on {0}'.format(msg))
                self.handle(msg)

    def handle(self, message):
        '''Iterates through the registered commands and attempts to find a
        command which matches the incoming Message. Does this by calling
        command.match() for each.
        '''
        for command in self.commands:
            log.debug('Checking command {}'.format(command.name))
            if command.match(message):  # the call
                log.info('{} matched!'.format(command.name))
                resp = command(message)
                log.info('Called command method {0}'.format(command.name))
                if resp:
                    log.info('Got a reply: {}'.format(resp))
                    # we have something to hand back
                    if type(resp) == str:
                        log.info('Response is a string, sending...')
                        self.conn.message(message.dest, resp)
                    elif isinstance(resp, GeneratorType):
                        log.info(
                            'Response is a generator, giving back the contents'
                        )
                        for reply in resp:
                            self.conn.message(message.dest, reply)
                break  # don't check any more methods
            else:
                log.debug(
                    '{0} failed to match {1}'.format(command.name, message)
                )

    @_builtin_command('^\.version')
    def version(self, message):
        '''display the library version'''
        return '{}: {} version {}'.format(message.nick, self.nick, VERSION)

    @_builtin_command('^\.ping')
    def ping(self, message):
        '''pong'''
        return '{}: pong'.format(message.nick)

    @_builtin_command('^\.join')
    def join_multi(self, message):
        '''join a number of channels'''
        if len(message.args) < 1:
            log.debug('Error for join_multi usage: not enough args')
            return 'Usage: .join #channelname'
        else:
            log.debug('We got channels: {}'.format(message.args))
            self.join(message.args)

    @_builtin_command('^\.help')
    def help(self, message):
        '''return name and description of all commands'''
        for command in self.commands:
            log.debug('Sending {} for command list'.format(command.name))
            yield '{}: {} - {}'.format(message.nick, command.name, str(command))
