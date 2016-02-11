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

    def recieve(self):
        ''' recieve from the socket, yield as a generator expression
        '''
        linesep = b'\r\n'
        format_msg = lambda x: (str(x[0], 'utf-8'), x[1])
        while True:
            # keep recieving until we get a \r\n
            read = self.conn.recv(self.recv_bufsz)
            while linesep in read:
                # pop of all the text up to/including \r\n
                message, read = format_msg(read.split(linesep, 1))
                if '\x01' in message:
                    message = message.replace('\x01', '')
                log.info('RECV {0}'.format(message))
                # handle PING/PONG
                if message.startswith('PING'):
                    self.send('PONG' + message[4:])
                else:
                    yield message

    def send(self, message):
        ''' helper method to convert the string,
        tack on a \r\n and log it
        '''
        self.conn.send(message.encode() + b'\r\n')
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
