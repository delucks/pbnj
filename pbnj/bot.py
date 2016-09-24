import sys
import argparse
import inspect
import logging
from types import GeneratorType

from pbnj.connection import Connection
from pbnj.models import Message, Command, _builtin_command
from pbnj.logger import ColorFormatter
from pbnj import __version__

log = logging.getLogger()
color_formatter = ColorFormatter()
sh = logging.StreamHandler()
sh.setFormatter(color_formatter)
log.addHandler(sh)


class Bot:
    def __init__(self, nick, username=None, realname=None, builtin_prefix='^\.'):
        self.nick = nick
        self.username = username or nick
        self.realname = realname or nick
        self.channels = []
        self.max_msg_len = 300
        self.commands = []
        self.conn = None
        self.builtin_prefix = builtin_prefix

    def _parse_args(self, arguments=sys.argv[1:], docstring=None, override=True):
        '''use argparse to give this Bot additional options from the CLI
        should be called when __name__ == __main__'''
        p = argparse.ArgumentParser(description=docstring or self.nick)
        p.add_argument('-n', '--nick', default=self.nick,
                       help='specify different nickname to use')
        p.add_argument('-d', '--debug', action='store_true',
                       help='increase logging verbosity to DEBUG')
        p.add_argument('-q', '--quiet', action='store_true',
                       help='decrease logging verbosity to WARNING')
        p.add_argument('-c', '--no-color', action='store_true',
                       help='disable coloration of logging output')
        p.add_argument('--network', default='127.0.0.1',
                       help='FQDN of IRC network to connect to')
        p.add_argument('--port', type=int, default=6667,
                       help='specify different port for the connection')
        p.add_argument('--channels',
                       help='comma-separated channels to connect to when joining')
        p.add_argument('--user-name', dest='username', default=self.username,
                       help='specify different name to use')
        p.add_argument('--real-name', dest='realname', default=self.realname,
                       help='specify different realname to use')
        args = p.parse_args(arguments)
        log_lvl = logging.DEBUG if args.debug else logging.WARNING if args.quiet else logging.INFO
        color_formatter.color_enabled=not args.no_color
        log.setLevel(log_lvl)
        if override:
            self.nick = args.nick
            self.username = args.username
            self.realname = args.realname
            self.connect(args.network, args.port)
        if args.channels:
            self.joinall(args.channels.split(','))
        return args

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

    def _activate_commands(self):
        '''check for _builtin_command decorated commands, insert them'''
        log.debug('Checking methods for builtin commands')
        for m_name, method in inspect.getmembers(self, inspect.ismethod):
            if '_command' in dir(method):
                log.debug('{} is a command!'.format(m_name))
                self.commands.append(Command(self.builtin_prefix + method._filterspec, method))
        log.debug(str(self.commands))

    def connect(self, addr, port=6667):
        '''create a connection to an address, or return one if it already exists'''
        if not self._is_connected():
            self.conn = Connection(addr, port, __version__)
        return self.conn

    def command(self, filterspec):
        def real_decorator(function):
            log.debug('Creating command for function {}'.format(function))
            c = Command(filterspec, function)
            self.commands.append(c)
            log.debug('Added to self.commands')
            return function
        log.debug('Exiting command() decorator')
        return real_decorator

    def join(self, channel):
        '''joins a channel'''
        self.channels.append(channel)
        return self.conn.join(channel)

    def joinall(self, channels):
        '''joins a bunch of channels'''
        success = True
        for channel in self._channelify(channels):
            self.channels.append(channel)
            success = success and self.conn.join(channel)
        return success

    def part(self, channels):
        '''leaves a bunch of channels :( '''
        for channel in self._channelify(channels):
            self.channels.remove(channel)
            self.conn.part(channel)

    def raw_send(self, message):
        '''deliver a message directly to the connection- useful for doing things
        like MODE'''
        return self.conn.send(message)

    def run(self):
        '''set up and connect the bot, start looping!'''
        self._activate_commands()
        # start the connection
        with self.conn:
            # make sure we're registered to the irc network
            self.conn.register(self.username, self.nick, self.conn.addr, self.realname)
            # handle any channels the user asked us to join
            if self.channels:
                log.info('Joining initial channels')
                for channel in self.channels:
                    self.conn.join(channel)
            for msg in self._messageify(self.conn.recieve()):
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
                        return self.conn.message(message.reply_dest, resp)
                    elif isinstance(resp, GeneratorType):
                        log.info(
                            'Response is a generator, giving back the contents'
                        )
                        success = True
                        for reply in resp:
                            success = success and self.conn.message(message.reply_dest, reply)
                        return success
                    elif isinstance(resp, bool):
                        logging.debug('the function handed back a boolean, returning it')
                        return resp
                    else:
                        log.warning('Got back a weird type from a command')
                        log.warning(resp)
                        return False
                break  # don't check any more methods
            else:
                log.debug(
                    '{0} failed to match {1}'.format(command.name, message)
                )
        log.debug('No matches found.')
        return False  # couldn't find a match for the command at all

    @_builtin_command('version')
    def version(self, message):
        '''display the library version'''
        return '{}: {} version {}'.format(message.nick, self.nick, __version__)

    @_builtin_command('ping')
    def ping(self, message):
        '''pong'''
        return '{}: pong'.format(message.nick)

    @_builtin_command('join')
    def join_multi(self, message):
        '''join a number of channels'''
        if len(message.args) < 1:
            log.debug('Error for join_multi usage: not enough args')
            return 'Usage: .join #channelname'
        else:
            log.debug('We got channels: {}'.format(message.args))
            return self.joinall(message.args)

    @_builtin_command('help')
    def help(self, message):
        '''return name and description of all commands'''
        for command in self.commands:
            log.debug('Sending {} for command list'.format(command.name))
            yield '{}: {} - {}'.format(message.nick, command.name, str(command))
