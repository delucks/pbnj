import pytest
import socket
import os
from unittest.mock import patch
from pbjbt.connection import IRCConnection

NICK = 'foo'
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
            curr_msg = self.messages.pop()
        else:
            curr_msg = None
        print(curr_msg)
        self.recieved.append(curr_msg)
        return curr_msg

@pytest.fixture
def mocked_connection():
    with patch('socket.socket', FakeSocket):
        c = IRCConnection(HOSTNAME, PORT)
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

def test_recv(registered_connection):
    fs = registered_connection.conn
    inspired = _get_log('InspIRCd-2.0.log')
    fs._set_reply_text(inspired)
    gotten = []
    for line in registered_connection.recieve():
        print(line) # rgggghrrfazdsalskdfj TODO
        gotten.append(line)
    assert gotten
