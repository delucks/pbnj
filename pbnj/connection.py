import ssl
import socket
import logging

log = logging.getLogger("pbnj")


class Connection:
    """sets up the bots connection on a socket level.
    The only *magic* this class does is respond to PING messages with PONG
    messages, which I see as an essential part of maintaining a Connection
    """

    def __init__(
        self, addr, port, version="-1", timeout=10.0, recv_bufsz=4096, use_ssl=False
    ):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if use_ssl or port == 6697:
            self.conn = ssl.wrap_socket(conn, cert_reqs=ssl.CERT_REQUIRED)
        else:
            self.conn = conn
        self.ssl = use_ssl
        self.addr = addr
        self.port = port
        self.version = version
        self.conn.settimeout(timeout)
        self.conn.setblocking(1)  # will block
        self.recv_bufsz = recv_bufsz
        self.read = b""
        self.linesep = b"\r\n"
        self._connected = False

    def __str__(self):
        return "pbnj.connection.Connection to {}:{}, ssl {}".format(
            addr, port, "on" if self.ssl else "off"
        )

    def __repr___(self):
        return self.__str__()

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, type, value, traceback):
        if self._connected:
            self._cleanup()

    def _cleanup(self):
        """close down everything that needs to be closed"""
        self.send("QUIT :{0}/{1}".format(self.nick, self.version))
        log.warning("Closing socket and IRC connections")
        self._connected = False
        self.conn.close()

    def _connect(self):
        """set up the socket connection and be ready for sending data"""
        # TODO: add retry logic
        try:
            self.conn.connect((self.addr, self.port))
            self._connected = True
        except ssl.SSLError:
            log.fatal("Failed to verify the connection to the server via SSL")
            raise

    def _is_termination_message(self, message):
        return "Closing link" in message or "Server going down" in message

    def _recv(self):
        """recieve only one line from the socket"""
        while self.linesep not in self.read:
            self.read += self.conn.recv(self.recv_bufsz)
        format_msg = lambda x: (str(x[0], "utf-8"), x[1])
        message, read = format_msg(self.read.split(self.linesep, 1))
        if "\x01" in message:
            message = message.replace("\x01", "")
        log.info("RECV {0}".format(message))
        if not message:
            log.warning("Got a null message from server")
            raise ConnectionException("Null message")
        elif self._is_termination_message(message):
            log.warning("Got a termination message from server")
            raise ConnectionException("Got a termination message")
        else:
            self.read = read
            return message

    def recieve(self):
        """recieve lines of text from our socket and return them as a Generator
        """
        connected = True
        while connected:
            try:
                message = self._recv()
                if message.startswith("PING"):
                    log.debug("Replying with PONG...")
                    self.send("PONG" + message[4:])
                else:
                    yield message
            except ConnectionException:
                connected = False
        self._cleanup()

    def send(self, message):
        """helper method to convert the string, tack on a \r\n and log it"""
        try:
            self.conn.send(message.encode() + b"\r\n")
            log.info("SEND " + message)
            return True
        except Exception as e:
            log.error("Hit an exception while trying to send {}".format(message))
            return False

    def part(self, channel):
        return self.send("PART {}".format(channel))

    def join(self, channel):
        if self._connected:
            return self.send("JOIN {}".format(channel))
        else:
            log.info(
                "Tried to join a channel before starting, will join when connected"
            )
            return False

    def message(self, channel, message):
        return self.send("PRIVMSG {0} :{1}".format(channel, message))

    def register(self, user, nick, hostname, realname=None):
        """send the needed info to the IRC server after connecting"""
        realname = user if not realname else realname
        self.nick = nick
        log.info(
            "Registering on network {0} with ({1}/{2}/{3})".format(
                self.addr, user, realname, hostname
            )
        )
        n = self.send("NICK {0}".format(nick))
        return n and self.send("USER {0} {0} {2} :{1}".format(user, realname, hostname))


class ConnectionException(Exception):
    pass
