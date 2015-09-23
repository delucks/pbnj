import socket
import logging
import sys
import re
import time

logging.basicConfig(format='%(asctime)s %(message)s', stream=sys.stderr, level=logging.DEBUG)
VERSION='0.01'

''' sets up the bots connection on a socket level.
exposes methods for closing, restarting, registering, and all the 
utility parts of the irc protocol
'''
class IRCConnection:
    def __init__(self, addr, port, timeout=10.0):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(10.0)
        self.conn.setblocking(1) # will block
    
    # set up the socket connection and be ready for sending data
    def __enter__(self):
        self.conn.connect((net, port))
        return self # TODO: check if this is an incorrect paradigm for __enter__s

    # close down everything that needs to be closed
    def __exit__(self, type, value, traceback):
        self.send('QUIT :pbjbt/' + VERSION)
        self.conn.close()

    # basic helper method to tack on a \r\n and log it
    def send(self, message):
        self.conn.send(message + '\r\n')
        logging.debug('SEND ' + message)

    def part(self, channel):
        self.send('PART {0}'.format(channel))

    def join(self, channel):
        self.send('JOIN {0}'.format(channel))

    def message(self, channel, message):
        self.send('PRIVMSG {0} :{1}'.format(channel, message))

    def recv_forever(self, recv_bufsz=4096):
        while True:
            read = self.conn.recv(recv_bufsz)
            while '\r\n' in read:
                spl = read.split('\r\n', 1)
                logging.info('RECV ' + spl[0])
                yield spl[0]
                read = spl[1]

    def register(self, user, nick, realname=None):
        realname = user if not realname else realname
        self.send('NICK {0}'.format(nick))
        hostname = socket.gethostname() # TODO: Add behavior to override the hostname detection
        self.send('USER {0} {0} {2} :{1}'.format(user, realname, hostname))

''' handles IRC interactions from a high level (user visible)
'''
class IRCBot:
    def __init__(self, nick, name, connection, realname=None, init_channels=None):
        self.nick = nick
        self.name = name
        self.conn = connection
        self.realname = realname
        self.channels = []
        self.init_channels = init_channels

    def join(self, channels):
        for channel in channels:
            self.channels.append(channel)
            self.conn.join(channel)

    def part(self, channels):
        for channel in channels:
            self.channels.remove(channel)
            self.conn.part(channel)

    # Parse the message into a convenient dictionary (TODO: direct log this as JSON?)
    def split_msg(self, message):
        m = re.match('^(?:[:](\S+) )?(\S+)(?: (?!:)(.+?))?(?: [:](.+))?$', message)
        g = m.groups()
        return {
                'hostmask': g[0],
                'type': g[1],
                'dest': g[2],
                'message': g[3]
        }

    # Make sure this method DOES NOT BLOCK! You can hold up the whole bot because it's single threaded!
    def handle(self, msg_object):
        if msg_object['type'] == 'PING':
            self.conn.send('PONG :' + msg_object['message'])
        if msg_object['dest'] == self.nick:
            # do something if someone messages you
            pass
        elif msg_object['dest'] in self.channels:
            # do something if there's a message that comes up in a channel you're in
            pass
        else:
            # do something! :D
            pass
        if msg_object['message']: # TODO: all of this could be simplified into a standard method
            if msg_object['message'].startswith('.join'):
                sp = msg_object['message'].split()
                if len(sp) < 2:
                    self.conn.message(msg_object['dest'], 'Usage: .join #channelname')
                else:
                    # TODO: add support for joining multiple channels 
                    chan = '#' + sp[1] if not sp[1].startswith('#') else sp[1]
                    self.join([chan])

    def run(self):
        self.conn.register(self.nick, self.name, self.realname)
        if self.init_channels is not None:
            self.join(self.init_channels)
        for recv_irc_msg in self.conn.recv_forever():
            split = self.split_msg(recv_irc_msg)
            self.handle(split) # this is why handle shouldn't block

#net = 'irc.lug.udel.edu'
net = '127.0.0.1'
port = 6667
#port = 6697

with IRCConnection(net, port) as c:
    bot = IRCBot(nick='pbjbt', name='pbjbt', connection=c, init_channels=['#foo'])
    bot.run()
