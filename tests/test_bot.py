import pytest
from random import choice
from pbjbt.bot import Bot
from pbjbt.models import Message, Command
from tests.common import _wrap, _get_log
from tests.common import *

def test_bot_init():
    b = Bot(NICK)
    assert NICK == b.username
    assert NICK == b.realname
    assert not b.conn, 'Connection was initialized'
    assert not b.commands, 'Command got inserted before run()'

def test_bot_is_connected(mocked_bot):
    assert not mocked_bot._is_connected()
    mocked_bot.connect(HOSTNAME, PORT)
    assert mocked_bot._is_connected()

@pytest.fixture()
def channels(mocked_bot):
    channels = list(mocked_bot._channelify(MALFORMED_CHANNELS))
    for c in channels:
        assert c.startswith('#')
    return channels

def test_messageify(connected_bot):
    fs = connected_bot.conn.conn
    inspired = _get_log('InspIRCd-2.0.log')
    inspired_messages = [Message(line) for line in inspired.splitlines()]
    for idx, mify_object in enumerate(connected_bot._messageify(inspired.splitlines())):
        assert mify_object == inspired_messages[idx]

def test_bot_join(connected_bot, channels):
    fs = connected_bot.conn.conn
    msgz = [_wrap('JOIN {}'.format(i)) for i in channels]
    with connected_bot.conn:
        connected_bot.join(MALFORMED_CHANNELS)
        for c in channels:
            assert c in connected_bot.channels
        for m in msgz:
            assert m in fs.sent

def test_command(connected_bot):
    fs = connected_bot.conn.conn
    def test_function(message):
        if m.type != 'PRIVMSG':
            return message
        else:
            return None
    inspired = _get_log('InspIRCd-2.0.log')
    connected_bot.command('pattern')(test_function)
    test_command = Command('pattern', test_function)
    assert test_command in connected_bot.commands
    i = connected_bot.commands.index(test_command)
    other = connected_bot.commands[i]
    assert test_command.callback == other.callback
    for i in range(RANDOM_TEST_RUNS):
        m = Message(choice(inspired.splitlines()))
        assert test_command.match(m) == other.match(m)
        assert test_command.callback(m) == other.callback(m)

def test_run(response_bot):
    fs = response_bot.conn.conn
    response_bot.run()

def test_handle(command_bot):
    fs = command_bot.conn.conn
    command_bot._activate_commands()
    inspired = fs.text.splitlines()
    for i in range(RANDOM_TEST_RUNS):
        selection = choice(inspired)
        idx = inspired.index(selection)
        m = Message(selection)
        if idx == len(inspired):
            assert not command_bot.handle(m)
        else:
            assert command_bot.handle(m)
