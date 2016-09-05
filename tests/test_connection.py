import pytest
import socket
import os
from unittest.mock import patch
from pbjbt.connection import Connection

NICK = 'foo'
CHANNEL = '#foo'
USER = 'bar'
REALNAME = 'baz'
HOSTNAME = 'localhost'
PORT = 6667

def _wrap(message):
    '''as if it was sent/recieved over a socket'''
    return bytes('{}\r\n'.format(message).encode('utf-8'))

def _get_log(logname):
    pwd = os.path.dirname(os.path.realpath(__file__))
    logs_dir = os.path.join(pwd, 'logs/')
    log_path = os.path.join(logs_dir, logname)
    with open(log_path) as f:
        return f.read()


class FakeSocket:
    '''why? I need to send predictable IRC messages to my bot without
    actually using the network, that's why!'''
    def __init__(self, s_family, s_type):
        self.sent = []  # this will hold all the stuff send() gets
        self.recieved = []
    def connect(self, dstspec):
        self.addr, self.port = dstspec
    def _set_reply_text(self, text):
        '''set the text we'll send to the socket'''
        self.text = text
        messages = []
        for line in self.text.splitlines():
            messages.append(_wrap(line))
            #print(messages)
        self.messages = messages
    def settimeout(self, timeout):
        pass
    def setblocking(self, val):
        pass
    def close(self):
        pass
    def send(self, message):
        self.sent.append(message)
    def recv(self, bufsz):
        # TODO don't throw away bufsz and actually return that much of our corpus
        if self.messages:
            curr_msg = self.messages.pop(0)
            #print(curr_msg)
        else:
            curr_msg = None
        self.recieved.append(curr_msg)
        return curr_msg

@pytest.fixture
def mocked_connection():
    with patch('socket.socket', FakeSocket):
        c = Connection(HOSTNAME, PORT)
        return c

@pytest.fixture
def registered_connection(mocked_connection):
    mocked_connection.register(USER, NICK, HOSTNAME, REALNAME)
    return mocked_connection

def test_register(mocked_connection):
    fs = mocked_connection.conn
    with mocked_connection:
        mocked_connection.register(USER, NICK, HOSTNAME, REALNAME)
        assert _wrap('NICK {}'.format(NICK)) in fs.sent
        assert _wrap('USER {0} {0} {2} :{1}'.format(USER, REALNAME, HOSTNAME)) in fs.sent
        assert mocked_connection.addr == HOSTNAME
        assert mocked_connection.port == PORT
    assert _wrap('QUIT :{}/{}'.format(NICK, mocked_connection.version)) in fs.sent

def test_send(registered_connection):
    fs = registered_connection.conn
    message = 'oh jeez rick'
    registered_connection.send(message)
    assert _wrap(message) in fs.sent

def test_message(registered_connection):
    fs = registered_connection.conn
    message = 'oh jeez rick'
    registered_connection.send(message)
    with registered_connection:
        registered_connection.message(CHANNEL, message)
        assert _wrap('PRIVMSG {} :{}'.format(CHANNEL, message)) in fs.sent

def test_recv(registered_connection):
    fs = registered_connection.conn
    reply = 'this is some sample \x01 text'
    fs._set_reply_text(reply)
    r = registered_connection._recv()
    assert r
    assert '\x01' not in r
    assert '\r\n' not in r
    assert reply.replace('\x01','') == r

def test_ping(registered_connection):
    fs = registered_connection.conn
    reply = '''PING :irc.foo.bar.baz\n
    PING :irc.foo.bar.baz\n
    '''
    fs._set_reply_text(reply)
    respones = []
    with registered_connection:
        for item in registered_connection.recieve():
            assert item
            responses.append(item)
        assert _wrap('PONG :irc.foo.bar.baz') in fs.sent

def test_join_part(registered_connection):
    fs = registered_connection.conn
    registered_connection.join(CHANNEL)
    with registered_connection:
        registered_connection.join(CHANNEL)
        assert _wrap('JOIN {}'.format(CHANNEL)) in fs.sent
        registered_connection.part(CHANNEL)
        assert _wrap('PART {}'.format(CHANNEL)) in fs.sent

def test_recieve(registered_connection):
    fs = registered_connection.conn
    inspired = _get_log('InspIRCd-2.0.log')
    fs._set_reply_text(inspired)
    gotten = []
    for line in registered_connection.recieve():
        assert fs.recieved
        gotten.append(line)
    #for line in inspired.splitlines():
    #    assert line in gotten
