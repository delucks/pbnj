import socket
import logging
import sys
import re
import time

logging.basicConfig(format='%(asctime)s %(message)s', stream=sys.stderr, level=logging.DEBUG)

''' sets up the bots connection on a socket level.
can expose methods like "send_msg" or "priv_msg" as a high-level interface,
with methods for closing, restarting, registering, and all the utility parts of the
irc protocol

notes:
should probably move recieving stuff to its own method, and make it use yield or something so we can call it like a generator
'''
class IRCConnection:
    def __init__(self, addr, port, timeout=10.0):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(10.0)
    
    # set up the socket connection and be ready for sending data
    def __enter__(self):
        self.conn.connect((net, port))
        return self

    # close down everything that needs to be closed
    def __exit__(self, type, value, traceback):
        self.conn.close()

    def send(self, message):
        self.conn.send(message + '\r\n')
        logging.debug('SEND ' + message)

    def join(self, channel):
        self.send('JOIN {0}'.format(channel))

    def recv_forever(self, recv_bufsz=1024):
        read = ''
        while 1:
            try:
                read = self.conn.recv(recv_bufsz)
                logging.info('RECV ' + read)
                yield read
            except socket.timeout:
                continue

    def send_rg_msg(self, user, nick, realname):
        time.sleep(1)
        self.send('NICK {0}'.format(nick))
        self.send('USER {0} {0} {0}.lug.udel.edu :{1}'.format(user, realname))
        self.recv_until('.*End of.*', self.join, ('#bot'))
        self.recv_forever()

    def register(self, user, nick, realname=None):
        if realname == None:
            realname = user
        # TODO some servers, wait for PING :randomstr and respond with PONG :randomstr
        # TODO: this doesn't work on servers that aren't running the kind of IRC server that irc.lug does
        self.recv_until('.*(resolve|Found) your hostname.*', self.send_rg_msg, (user, nick, realname))

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
        if cb_args is not None:
            callback(*cb_args)
        else:
            callback()

net = 'irc.lug.udel.edu'
#net = 'snowball.lug.udel.edu'
port = 6667

with IRCConnection(net, port) as c:
    c.register('pbjbt', 'pbjbt')
