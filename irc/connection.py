# -*- coding: utf-8 -*-
import socket
import logging
log = logging.getLogger()


class IRCConnection(object):
    ''' sets up the bots connection on a socket level.
    exposes methods for closing, restarting, registering, and all the
    utility parts of the irc protocol
    '''
    def __init__(self, addr, port, version='-1', timeout=10.0, recv_bufsz=4096):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = addr
        self.port = port
        self.version = version
        self.conn.settimeout(timeout)
        self.conn.setblocking(1)  # will block
        self.recv_bufsz = recv_bufsz

    def __enter__(self):
        ''' set up the socket connection and be ready for sending data
        '''
        self.conn.connect((self.addr, self.port))
        return self

    def __exit__(self, type, value, traceback):
        ''' close down everything that needs to be closed
        '''
        self.send('QUIT :{0}/{1}'.format(self.nick, self.version))
        self.conn.close()

    def __call__(self):
        ''' recieve from the socket, yield as a generator expression
        '''
        while True:
            read = self.conn.recv(self.recv_bufsz)
            # keep recieving until we get a \r\n, also strip out junk chars
            if '\x01' in read:
                read = read.replace('\x01', '')
            while '\r\n' in read:
                spl = read.split('\r\n', 1)
                # pop of all the text up to/including \r\n
                log.info('RECV ' + spl[0])
                yield spl[0]
                # reassign to the non-split portion
                read = spl[1]

    def send(self, message):
        ''' basic helper method to tack on a \r\n and log it
        '''
        self.conn.send(message + '\r\n')
        log.info('SEND ' + message)

    def part(self, channel):
        self.send('PART {0}'.format(channel))

    def join(self, channel):
        self.send('JOIN {0}'.format(channel))

    def message(self, channel, message):
        self.send('PRIVMSG {0} :{1}'.format(channel, message))

    def register(self, user, nick, hostname, realname=None):
        realname = user if not realname else realname
        self.nick = nick
        self.send('NICK {0}'.format(nick))
        self.send('USER {0} {0} {2} :{1}'.format(user, realname, hostname))
        log.info('Registered on network {0} with ({1}/{2}/{3})'.format(
            self.addr, user, realname, hostname))

#def connection_thread(
