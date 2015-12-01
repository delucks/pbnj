#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import logging
import sys
import re
import time
import argparse
import inspect
from collections import OrderedDict

'''
Samples of strings coming in we may see
    :nick!username@hostname.net JOIN :#channel
    :nick!username@hostname.net PRIVMSG #channel :message context
    :hostmask QUIT :Quit:WeeChat 0.4.2
    :fqdn.net 002 nick :Your host is irc.fqdn.net, running FooIRCd-0.1
'''
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
channelize = lambda x: ['#'+c if not c.startswith('#') else c for c in x]
return_votes = lambda x: 'voted {0} (+{1}/-{2})'.format(x[0]-x[1], x[0], x[1])
VERSION = '0.04'


class IRCConnection(object):
    ''' sets up the bots connection on a socket level.
    exposes methods for closing, restarting, registering, and all the
    utility parts of the irc protocol
    '''
    def __init__(self, addr, port, timeout=10.0, recv_bufsz=4096):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = addr
        self.port = port
        self.conn.settimeout(timeout)
        self.conn.setblocking(1)  # will block
        self.log = []  # TODO: __getitem__?
        self.recv_bufsz = recv_bufsz

    def __enter__(self):
        ''' set up the socket connection and be ready for sending data
        '''
        self.conn.connect((self.addr, self.port))
        return self

    def __exit__(self, type, value, traceback):
        ''' close down everything that needs to be closed
        '''
        self.send('QUIT :pbjbt/' + VERSION)
        self.conn.close()

    def send(self, message):
        ''' basic helper method to tack on a \r\n and log it
        '''
        self.conn.send(message + '\r\n')
        logging.info('SEND ' + message)

    def part(self, channel):
        self.send('PART {0}'.format(channel))

    def join(self, channel):
        self.send('JOIN {0}'.format(channel))

    def message(self, channel, message):
        self.send('PRIVMSG {0} :{1}'.format(channel, message))

    def recv_forever(self):
        while True:
            read = self.conn.recv(self.recv_bufsz)
            # keep recieving until we get a \r\n, also strip out junk chars
            if '\x01' in read:
                read = read.replace('\x01', '')
            while '\r\n' in read:
                spl = read.split('\r\n', 1)
                # pop of all the text up to/including \r\n
                logging.info('RECV ' + spl[0])
                yield spl[0]
                # reassign to the non-split portion
                read = spl[1]

    def register(self, user, nick, hostname, realname=None):
        realname = user if not realname else realname
        self.send('NICK {0}'.format(nick))
        self.send('USER {0} {0} {2} :{1}'.format(user, realname, hostname))


def wrap_command(func, cmd_regex, arg_handling):
    ''' Decorator to match a regular expression against messages
    then modify the arguments to the decorated function to pull out
    different properties of the message.
    The last argument will always be filled in by the macro
    The regex and handling stragegy get read by the macro and stay static
    The checks in the beginning which return False are for early termination of
    the method before we hit any expensive code paths (regex'ing the message)
    '''
    def wrapped(*args):
        msg_object = args[1]
        # commands only apply to private/public messages and /me
        if msg_object['type'] == 'PRIVMSG' or msg_object['type'] == 'ACTION':
            message = msg_object['message']
            match = re.match(cmd_regex, message)
            if not match:
                logging.debug('{0} failed to match {1}'.format(
                    func.__name__, message)
                )
                return False
            if arg_handling == 'group':
                newargs = (args[0], args[1], match.groups())
            elif arg_handling == 'first':
                newargs = (args[0], args[1], message.split()[1])
            elif arg_handling == 'pass':
                newargs = (args[0], args[1], message.split()[1:])
            else:  # none
                newargs = args
            logging.debug('wrap_command calling {0} with {1}'.format(
                func.__name__, newargs)
            )
            func(*newargs)
        else:
            return False
    return wrapped


def bot_command(cmd_regex, arg_handling):
    ''' marks a method as a command within a subclass of IRCBot.
    It can then interact with incoming irc messages after the
    class is activated with @activebot()
    '''
    def command_decorator(func):
        func._cmd = True
        func._cmd_regex = cmd_regex
        func._arg_handling = arg_handling
        return func
    return command_decorator


def activebot():
    ''' marks a subclass of IRCBot as the active bot to use.
    Activates all of the @bot_command(...) commands by decorating
    them with wrap_command(...)
    '''
    def wrap_bot_class(bot_class):
        for m_name, method in inspect.getmembers(bot_class, inspect.ismethod):
            if '_cmd' in dir(method):  # this is SO HACKY
                # this is a command method, and needs to be decorated
                wrapped = wrap_command(
                    method, method._cmd_regex, method._arg_handling
                )
                bot_class.commands[m_name] = wrapped
                # we're manually decorating because fuck you iteration
                setattr(bot_class, m_name, wrapped)
        return bot_class
    return wrap_bot_class


class IRCBot(object):
    ''' handles IRC interactions from a higher level (common utility functions)
    Subclass this in order to build a working bot.
    '''
    # this is in the class scope so it can be modified by activebot
    commands = OrderedDict()
    # replace this with another class that can have more
    # metadata about each command TODO

    def __init__(self):
        raise NotImplementedError(
            'You must subclass IRCBot, then call create()'
        )

    def create(self, connection, nick, name,
               hostname, realname, init_channels):
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
        self.max_msg_len = 300

    def join(self, channels):
        ''' joins a bunch of channels
        '''
        for channel in channels:
            self.channels.append(channel)
            self.conn.join(channel)

    def part(self, channels):
        ''' leaves a bunch of channels :(
        '''
        for channel in channels:
            self.channels.remove(channel)
            self.conn.part(channel)

    def split_hostmask(self, hostmask):
        m = re.match('^([a-zA-Z0-9]+)!~([a-zA-Z0-9\ ]+)@(.*)', hostmask)
        g = m.groups()
        return {
            'nick': g[0],
            'realname': g[1],
            'host': g[2],  # making this the same as the msg parsing tree
        }

    ''' Parse the message into a convenient dictionary
    TODO? direct log this as JSON
    Could we maybe use a namedtuple as data transport instead? Might be faster
    '''
    def split_msg(self, msg_source):
        for message in msg_source:
            if message.startswith(':'):
                # we really don't need to parse leading : from old servers
                message = message[1:]
            sp = message.split()
            host = sp[0]
            info = {}
            if not '@' in host:
                # this is a server directly sending us something or pinging us
                if host == 'PING':
                    m = ' '.join(sp[1:])
                    info['message'] = m[1:] if m.startswith(':') else m
                    msg_type = 'PING'
                else:
                    info['host'] = host
                    code = sp[1]
                    msg_type = int(code) if code.isdigit() else code
            else:
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
        self.conn.register(self.nick, self.name, self.realname)
        if self.init_channels:
            logging.debug('IRCBotBase: Joining initial channels')
            self.join(self.init_channels)
        for split in self.split_msg(self.conn.recv_forever()):
            logging.debug('IRCBotBase: Calling handle() on {0}'.format(split))
            self.handle(split)  # this is why handle shouldn't block

    def handle(self, msg_object):
        ''' takes a split message object and calls every command method
        The command methods will early-terminate with False returned
        if not applicable.
        Make sure they do not block, this whole thing is single-threaded
        '''
        if msg_object['type'] == 'PING':
            self.conn.send('PONG :' + msg_object['message'])
        else:
            for m_name, method in self.commands.iteritems():
                if method(self, msg_object):  # the call
                    logging.info('Called command method {0}'.format(m_name))
                else:
                    logging.debug(
                        '{0} failed to match {1}'.format(m_name, msg_object)
                    )

    @bot_command('^\.join', 'pass')
        ''' Commands in common between every IRCBot subclass:
        '''
    def join_multi(self, msg_object, channels):
        if len(channels) < 1:
            self.conn.message(
                msg_object['dest'],
                'Usage: .join #channelname'
            )
            return False  # this now early terminates
        logging.debug('We have channels! joining them.')
        chans = channelize(channels)
        self.join(chans)

    @bot_command('^\.version', 'none')
    def version(self, msg_object):
        nick = msg_object['nick']
        self.conn.message(
            msg_object['dest'],
            '{2}: {0} version {1}'.format(self.nick, VERSION, nick)
        )

    @bot_command('^\.ping', 'none')
    def ping(self, msg_object):
        nick = msg_object['nick']
        self.conn.message(
            msg_object['dest'],
            '{0}: pong'.format(nick)
        )

    @bot_command('^\.commands', 'none')
    def list_commands(self, msg_object):
        # TODO: use docstring of each method for its help text
        nick = msg_object['nick']
        self.conn.message(
            msg_object['dest'],
            '{0}: {1}'.format(nick, ','.join(self.commands.keys()))
        )


@activebot()
class pbjbt(IRCBot):
    ''' pbjbt is a simple bot. it uses 'pbjbt' for
    all of its names, and only has the ability to modify
    the origin hostname
    '''
    def __init__(self, connection, hostname, init_channels):
        self.votes = {}  # TODO some kind of session persistence
        super(pbjbt, self).create(
            connection,
            self.__class__.__name__,  # nick
            self.__class__.__name__,  # name
            hostname,
            self.__class__.__name__,  # realname
            init_channels
        )

    @bot_command('shrug', 'none')
    def shrug(self, msg_object):
        if msg_object['type'] == 'ACTION':
            self.conn.message(
                msg_object['dest'],
                '¯\_(ツ)_/¯'
            )

    @bot_command('^([a-zA-Z0-9]+)(\+\+|--|\*\*)', 'group')
    def increment(self, msg_object, match_groups):
        topic = match_groups[0]
        oper = match_groups
        if topic in self.votes:
            if match_groups[1] == '**':
                self.votes[topic][0] *= 2
            else:
                idx = 0 if match_groups[1] == '++' else 1
                self.votes[topic][idx] += 1
        else:
            self.votes[topic] = [1, 0] if match_groups[1] == '++' else [0, 1]
        if len(str(self.votes[topic][0])) > self.max_msg_len:
            self.votes[topic][0] = 0
            self.conn.message(
                msg_object['dest'],
                'You flew too close too the sun. Enthusiastic voting though!'
            )
        else:
            self.conn.message(
                msg_object['dest'],
                '{0}: {1}'.format(topic, return_votes(self.votes[topic]))
            )


def interactive():
    p = argparse.ArgumentParser(description='pbjbt')
    p.add_argument('-n', '--network', default='127.0.0.1',
                   help='FQDN of IRC network to connect to')
    p.add_argument('-p', '--port', type=int, default=6667,
                   help='specify different port for the connection')
    p.add_argument('--nick', default='pbjbt',
                   help='specify different nickname to use')
    p.add_argument('--name', default='pbjbt',
                   help='specify different name to use')
    p.add_argument('--real-name', dest='realname', default='pbjbt',
                   help='specify different realname to use')
    p.add_argument('--hostname', default=socket.gethostname(),
                   help='specify different hostname to use')
    p.add_argument('--debug', action='store_true',
                   help='increase logging verbosity to DEBUG')
    p.add_argument('-c', '--channels', nargs='+',
                   help='channels the bot will join immediately')
    args = p.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.channels:
        args.channels = channelize(args.channels)
    with IRCConnection(args.network, args.port) as c:
        bot = pbjbt(
            connection=c,
            hostname=args.hostname,
            init_channels=args.channels
        )
        bot.run()

if __name__ == '__main__':
    interactive()
