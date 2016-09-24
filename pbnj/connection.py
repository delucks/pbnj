import ssl
import socket
import logging
log = logging.getLogger()


class Connection:
    '''sets up the bots connection on a socket level.
    The only *magic* this class does is respond to PING messages with PONG
    messages, which I see as an essential part of maintaining a Connection
    '''
    def __init__(self, addr, port, version='-1', timeout=10.0, recv_bufsz=4096, use_ssl=False):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if use_ssl or port == 6697:
            self.conn = ssl.wrap_socket(conn, cert_reqs=ssl.CERT_REQUIRED)
        else:
            self.conn = conn
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
        try:
            self.conn.connect((self.addr, self.port))
            self._connected = True
            return self
        except ssl.SSLError:
            log.fatal('Failed to verify the connection to the server via SSL')
            raise

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
        try:
            self.conn.send(message.encode() + b'\r\n')
            log.info('SEND ' + message)
            return True
        except Exception as e:
            log.error('Hit an exception while trying to send {}'.format(message))
            return False

    def part(self, channel):
        return self.send('PART {}'.format(channel))

    def join(self, channel):
        if self._connected:
            return self.send('JOIN {}'.format(channel))
        else:
            log.info('Tried to join a channel before starting, will join when connected')
            return False

    def message(self, channel, message):
        return self.send('PRIVMSG {0} :{1}'.format(channel, message))

    def register(self, user, nick, hostname, realname=None):
        '''send the needed info to the IRC server after connecting'''
        realname = user if not realname else realname
        self.nick = nick
        log.info('Registering on network {0} with ({1}/{2}/{3})'.format(
            self.addr, user, realname, hostname))
        n = self.send('NICK {0}'.format(nick))
        return n and self.send('USER {0} {0} {2} :{1}'.format(user, realname, hostname))
