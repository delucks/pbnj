import pytest
from pbnj.connection import Connection
from common import _get_log, _wrap
from common import *
import logging
log = logging.getLogger('pbnj')
log.setLevel(logging.DEBUG)

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
    assert registered_connection.send(message)
    assert _wrap(message) in fs.sent

def test_message(registered_connection):
    fs = registered_connection.conn
    message = 'oh jeez rick'
    assert registered_connection.send(message)
    assert registered_connection.message(CHANNEL, message)
    assert _wrap('PRIVMSG {} :{}'.format(CHANNEL, message)) in fs.sent
    registered_connection.conn = None
    assert not registered_connection.send(message)

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
    for item in registered_connection.recieve():
        assert item
        responses.append(item)
    assert _wrap('PONG :irc.foo.bar.baz') in fs.sent

def test_join_part(registered_connection):
    fs = registered_connection.conn
    assert not registered_connection.join(CHANNEL)
    with registered_connection:
        assert registered_connection.join(CHANNEL)
        assert _wrap('JOIN {}'.format(CHANNEL)) in fs.sent
        assert registered_connection.part(CHANNEL)
        assert _wrap('PART {}'.format(CHANNEL)) in fs.sent

def test_recieve(registered_connection):
    fs = registered_connection.conn
    inspired = _get_log('InspIRCd-2.0.log')
    fs._set_reply_text(inspired)
    gotten = []
    for line in registered_connection.recieve():
        assert fs.recieved
        gotten.append(line)
    # the final line isn't recorded as it's the trigger for termination
    for line in inspired.splitlines()[:-1]:
        assert line.replace('\x01','') in gotten
