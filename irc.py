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

can recieve PING messages at any time, must respond with PONG within {timeout} secs or we'll get kicked
maybe we should make this class magic- you just instantiate it and then call it in a looop/generator expression to deliver all of your delicious utf-8 goodness
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
        self.conn.close()

    def send(self, message):
        self.conn.send(message + '\r\n')
        logging.debug('SEND ' + message)

    def join(self, channel):
        self.send('JOIN {0}'.format(channel))

    '''
    there must be a better way to do this
        maybe something like we recv infinitely, then fire off callback methods if a regex matches?
        pass in a dict of regex -> callbacks?
    alternately, we could use polymorphism
        like an IRCconnection is a generic handler class that defines a method that recv's forever, passing off each line to a predefined
        method that you can override in the subclasses
    alternately, we could make a container class that holds an IRCConnection as a property
        then, that class could consume events from the recv_forever() kinda method and decide on its own callbacks
    '''
    def recv_forever(self, recv_bufsz=1024):
        read = ''
        while True:
            try:
                read = self.conn.recv(recv_bufsz)
                if read.strip() == '':
                    continue
                logging.info('RECV ' + read)
                yield read
            except socket.timeout:
                print 'Got a socket.timeout, carrying on'
                continue

    def send_rg_msg(self, user, nick, realname):
        time.sleep(1)
        self.send('NICK {0}'.format(nick))
        hostname = socket.gethostname() # TODO: Add behavior to override the hostname detection
        self.send('USER {0} {0} {2} :{1}'.format(user, realname, hostname))

    def register(self, user, nick, realname=None):
        if realname == None:
            realname = user
        # TODO some servers, wait for PING :randomstr and respond with PONG :randomstr
        # TODO: this doesn't work on servers that aren't running the kind of IRC server that irc.lug does
        self.send_rg_msg(user, nick, realname)

    ''' usage: recv_until('^PING :([a-z]+)', self.pong, 'foo second argument')
    this'll call self.pong with the matching group of the regex as the first argument
    and the string provided as the second
    TODO: Delete this and move to something more elegant
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

#net = 'irc.lug.udel.edu'
net = '127.0.0.1'
port = 6667
#port = 6697

with IRCConnection(net, port) as c:
    c.register('pbjbt', 'pbjbt')
    c.join('#foo')
    # we just need to make sure to call recv_forever() like a generator
    for item in c.recv_forever():
        if 'foobar' in item:
            c.join('#bot')
        print item
