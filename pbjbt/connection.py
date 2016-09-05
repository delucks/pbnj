import socket
import logging
log = logging.getLogger()


class Connection:
    '''sets up the bots connection on a socket level.
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
        self.read = b''
        self.linesep = b'\r\n'
        self._connected = False

    def __enter__(self):
        '''set up the socket connection and be ready for sending data'''
        self.conn.connect((self.addr, self.port))
        self._connected = True
        return self

    def __exit__(self, type, value, traceback):
        '''close down everything that needs to be closed'''
        self.send('QUIT :{0}/{1}'.format(self.nick, self.version))
        log.warning('Closing socket and IRC connections')
        self._connected = False
        self.conn.close()

    def _recv(self):
        '''recieve only one line from the socket'''
        while self.linesep not in self.read:
            self.read += self.conn.recv(self.recv_bufsz)
        format_msg = lambda x: (str(x[0], 'utf-8'), x[1])
        message, read = format_msg(self.read.split(self.linesep, 1))
        if '\x01' in message:
            message = message.replace('\x01', '')
        log.info('RECV {0}'.format(message))
        if not message or 'Closing link' in message:
            log.warning('Got a "Closing link" message back from server')
            return None  # termination of loop
        self.read = read
        return message

    def recieve(self):
        '''turn recieving from the socket into a generator!'''
        while True:
            message = self._recv()
            if not message:
                log.warning('Got back None, terminating the recv loop')
                break
            elif message.startswith('PING'):
                log.debug('Replying with PONG...')
                self.send('PONG' + message[4:])
            else:
                yield message

    def send(self, message):
        '''helper method to convert the string, tack on a \r\n and log it'''
        self.conn.send(message.encode() + b'\r\n')
        log.info('SEND ' + message)

    def part(self, channel):
        self.send('PART {}'.format(channel))

    def join(self, channel):
        if self._connected:
            self.send('JOIN {}'.format(channel))
        else:
            log.error('Someone tried to join a channel before starting')

    def message(self, channel, message):
        self.send('PRIVMSG {0} :{1}'.format(channel, message))

    def register(self, user, nick, hostname, realname=None):
        '''send the needed info to the IRC server after connecting'''
        realname = user if not realname else realname
        self.nick = nick
        self.send('NICK {0}'.format(nick))
        self.send('USER {0} {0} {2} :{1}'.format(user, realname, hostname))
        log.info('Registered on network {0} with ({1}/{2}/{3})'.format(
            self.addr, user, realname, hostname))
