import socket
import logging
import sys
import re

logging.basicConfig(format='%(asctime)s %(message)s', stream=sys.stderr, level=logging.DEBUG)

''' sets up the bots connection on a socket level.
can expose methods like "send_msg" or "priv_msg" as a high-level interface,
with methods for closing, restarting, registering, and all the utility parts of the
irc protocol

notes:
should probably move recieving stuff to its own method, and make it use yield or something so we can call it like a generator
we may consider having __enter__/__exit__ methods so we can use this like:
    with IRCConnection() as irc:
        irc.register(...)
some kind of recv_until('PING...', callback_method, call_back_args) would be super useful
'''
class IRCConnection:
    def __init__(self, addr, port, timeout=10.0):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(10.0)
        self.conn.connect((net, port)) # would move to __enter__ if we do that

    def send(self, message):
        self.conn.send(message)
        logging.debug('SEND ' + message)

    def register(self, user, nick, realname=None):
        if realname == None:
            realname = user
        # some servers, wait for PING :randomstr and respond with PONG :randomstr
        read = ''
        while 1:
            try:
                read = self.conn.recv(1024)
                logging.info('RECV ' + read)
            except socket.timeout:
                self.send('NICK {0}\r\n'.format(nick))
                self.send('USER {0} 0 * :{1}'.format(user, realname))
                break

    ''' usage: recv_until('^PING :([a-z]+)', self.pong, 'foo second argument')
    this'll call self.pong with the matching group of the regex as the first argument
    and the string provided as the second
    STILL UNDER CONSTRUCTION
    '''
    def recv_until(self, break_rx, callback, cb_args, recv_bufsz=1024):
        broken = False
        buf = ''
        break_regex = re.compile(break_rx)
        while not broken:
            buf = self.conn.recv(recv_bufsz)
            logging.info('RECV ' + buf)
            # leave loop if we match the buffer with our regex
            if break_regex.match(buf):
                # TODO: add pulling out the matching group from the regex to supply to callback()
                logging.info('BREAK ON ' + break_rx)
                broken = True
        # this function should do some kind of send action
        callback(cb_args)

net = 'irc.lug.udel.edu'
#net = 'snowball.lug.udel.edu'
port = 6667

c = IRCConnection(net, port)
c.register('test', 'test_bot')
