#!/usr/bin/env python
import logging
import socket
import sys
import argparse

from irc.connection import IRCConnection
from irc.utility import bot_command
from irc.bot import IRCBot
VERSION = '0.05'


class pbjbt(IRCBot):
    ''' pbjbt is a simple bot. it uses 'pbjbt' for
    all of its names, and only has the ability to modify
    the origin hostname
    '''
    def __init__(self, connection, hostname, init_channels, version):
        self.votes = {}  # TODO some kind of session persistence
        super(pbjbt, self).create(
            connection,
            self.__class__.__name__,  # nick
            self.__class__.__name__,  # name
            hostname,
            self.__class__.__name__,  # realname
            init_channels,
            version
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
        return_votes = lambda x: 'voted {0} (+{1}/-{2})'.format(x[0]-x[1], x[0], x[1])
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
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    with IRCConnection(args.network, args.port, version=VERSION) as c:
        bot = pbjbt(
            connection=c,
            hostname=args.hostname,
            init_channels=args.channels,
            version=VERSION
        )
        bot.run()

if __name__ == '__main__':
    interactive()
