import pytest
from unittest.mock import patch
from pbnj.connection import Connection
from pbnj.bot import Bot
from pbnj.models import Message
from tests.common import _wrap, _get_log
from tests.common import *

@pytest.fixture
def mocked_connection():
    with patch('socket.socket', FakeSocket):
        c = Connection(HOSTNAME, PORT)
        return c

@pytest.fixture
def registered_connection(mocked_connection):
    mocked_connection.register(USER, NICK, HOSTNAME, REALNAME)
    return mocked_connection

@pytest.fixture
def mocked_bot():
    return Bot(NICK)

@pytest.fixture
def connected_bot(registered_connection, mocked_bot):
    mocked_bot.conn = registered_connection
    return mocked_bot

@pytest.fixture
def response_bot(connected_bot):
    fs = connected_bot.conn.conn
    inspired = _get_log('InspIRCd-2.0.log')
    fs._set_reply_text(inspired)
    return connected_bot

@pytest.fixture
def command_bot(connected_bot):
    fs = connected_bot.conn.conn
    inspired = _get_log('command.log')
    fs._set_reply_text(inspired)
    return connected_bot

@pytest.fixture
def privmsg():
    return Message(SAMPLE_PRIV)

@pytest.fixture
def actionmsg():
    return Message(SAMPLE_ACTION)

@pytest.fixture
def servermsg():
    return Message(SAMPLE_SERVER)

@pytest.fixture()
def channels(mocked_bot):
    channels = list(mocked_bot._channelify(MALFORMED_CHANNELS))
    for c in channels:
        assert c.startswith('#')
    return channels
