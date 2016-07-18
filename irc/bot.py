from irc.utility import bot_command, wrap_command

from collections import OrderedDict
import re
import inspect
import logging
log = logging.getLogger()


class IRCBot:
    ''' handles IRC interactions from a higher level (common utility functions)
    Subclass this in order to build a working bot.
    '''

    def __init__(self):
        #TODO change this.
        raise NotImplementedError(
            'You must subclass IRCBot, then call create()'
        )

    def create(self, connection, nick, name,
               hostname, realname, init_channels,
               version='-1'):
        ''' initializes a subclass of IRCBot.
        Done this way so you cannot directly initialize this class
        '''
        self.nick = nick
        self.name = name
        self.conn = connection
        self.realname = realname
        self.hostname = hostname
        self.channels = []
        self.init_channels = init_channels
        self.version = version
        self.max_msg_len = 300
        # replace this with another class that can have more
        # metadata about each command TODO
        self.commands = OrderedDict()

    def join(self, channels):
        ''' joins a bunch of channels
        '''
        channelize = lambda x: [c if c.startswith('#') else '#'+c for c in x]
        for channel in channelize(channels):
            self.channels.append(channel)
            self.conn.join(channel)

    def part(self, channels):
        ''' leaves a bunch of channels :(
        '''
        for channel in channels:
            self.channels.remove(channel)
            self.conn.part(channel)

    def split_hostmask(self, hostmask):
        # TODO remove dependence on regular expressions
        m = re.match('^([a-zA-Z0-9]+)!~([a-zA-Z0-9\ ]+)@(.*)', hostmask)
        g = m.groups()
        return {
            'nick': g[0],
            'realname': g[1],
            'host': g[2],  # making this the same as the msg parsing tree
        }

    ''' Parse the message into a convenient dictionary
    Could we maybe use a namedtuple as data transport instead? Might be faster
    '''
    def split_msg(self, msg_source):
        for message in msg_source:
            sp = message.split()
            host = sp[0]
            info = {}
            if not '@' in host:
                # this is a server directly sending us something
                info['host'] = host
                code = sp[1]
                msg_type = int(code) if code.isdigit() else code
            else:
                host = host[1:] if host.startswith(':') else host
                x = self.split_hostmask(host)
                info.update(x)  # merge the hostmask stuff back into 'info'
                msg_type = sp[1]
            if msg_type == 'PRIVMSG':
                destination = sp[2]
                info['dest'] = destination
                m = ' '.join(sp[3:])
                msg = m[1:] if m.startswith(':') else m
                if msg.startswith('ACTION'):
                    msg_type = 'ACTION'
                    msg = msg[7:]  # actions are privmsgs, why
                info['message'] = msg
            # TODO handle all the numeric ones
            info['raw_msg'] = message
            info['type'] = msg_type
            yield info

    def run(self):
        ''' set up the bot, join initial channels, start the loop
        '''
        for m_name, method in inspect.getmembers(self, inspect.ismethod):
            logging.debug('Checking if method {0} is a command...'.format(m_name))
            if '_cmd' in dir(method):  # this is SO HACKY
                logging.debug('{0} is a command!'.format(m_name))
                # this is a command method, and needs to be decorated
                wrapped = wrap_command(
                    method, method._cmd_regex, method._arg_handling
                )
                wrapped._cmd_regex = method._cmd_regex
                self.commands[m_name] = wrapped
                setattr(self, m_name, wrapped)
        self.conn.register(self.nick, self.name, self.realname)
        if self.init_channels:
            log.debug('Joining initial channels')
            self.join(self.init_channels)
        for split in self.split_msg(self.conn.recieve()):
            log.debug('Calling handle() on {0}'.format(split))
            self.handle(split)  # this is why handle shouldn't block

    def handle(self, msg_object):
        ''' takes a split message object and calls every command method
        The command methods will early-terminate with False returned
        if not applicable.
        Make sure they do not block, this whole thing is single-threaded
        '''
        for m_name, method in self.commands.items():
            logging.debug('Calling {0} with {1}'.format(m_name, msg_object))
            if method(self, msg_object):  # the call
                log.info('Called command method {0}'.format(m_name))
            else:
                log.debug(
                    '{0} failed to match {1}'.format(m_name, msg_object)
                )

    @bot_command('^\.join', 'pass')
    def join_multi(self, msg_object, channels):
        ''' join a number of channels
        '''
        if len(channels) < 1:
            self.conn.message(
                msg_object['dest'],
                'Usage: .join #channelname'
            )
            return False  # this now early terminates
        log.debug('We have channels! joining them.')
        self.join(channels)

    @bot_command('^\.version', 'none')
    def version(self, msg_object):
        ''' return bot version
        '''
        nick = msg_object['nick']
        self.conn.message(
            msg_object['dest'],
            '{2}: {0} version {1}'.format(self.nick, self.version, nick)
        )

    @bot_command('^\.ping', 'none')
    def ping(self, msg_object):
        ''' return "pong"
        '''
        nick = msg_object['nick']
        self.conn.message(
            msg_object['dest'],
            '{0}: pong'.format(nick)
        )

    @bot_command('^\.commands|^\.help', 'none')
    def list_commands(self, msg_object):
        ''' list all registered bot commands
        '''
        nick = msg_object['nick']
        self.conn.send('{0}: help format "regex applied: output"'.format(nick))
        for m_name, method in self.commands.items():
            name = method._cmd_regex or m_name
            docstring = ':' + method.__doc__ if method.__doc__ else ''
            log.debug('Sending {0} {1} for command list'.format(name, docstring))
            self.conn.message(
                msg_object['dest'],
                '{1} - {2}'.format(nick, name, docstring)
            )
