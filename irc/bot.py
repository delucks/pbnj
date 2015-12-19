# -*- coding: utf-8 -*-
from utility import bot_command

from collections import OrderedDict
import re
import logging
log = logging.getLogger()


class IRCBot(object):
    ''' handles IRC interactions from a higher level (common utility functions)
    Subclass this in order to build a working bot.
    '''
    # this is in the class scope so it can be modified by active_bot
    commands = OrderedDict()
    # replace this with another class that can have more
    # metadata about each command TODO

    def __init__(self):
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
            log.debug('IRCBotBase: Joining initial channels')
            self.join(self.init_channels)
        for split in self.split_msg(self.conn.recv_forever()):
            log.debug('IRCBotBase: Calling handle() on {0}'.format(split))
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
                    log.info('Called command method {0}'.format(m_name))
                else:
                    log.debug(
                        '{0} failed to match {1}'.format(m_name, msg_object)
                    )

    @bot_command('^\.join', 'pass')
    def join_multi(self, msg_object, channels):
        ''' Commands in common between every IRCBot subclass:
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
        nick = msg_object['nick']
        self.conn.message(
            msg_object['dest'],
            '{2}: {0} version {1}'.format(self.nick, self.version, nick)
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


