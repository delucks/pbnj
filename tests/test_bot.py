import pytest
from random import choice
from pbjbt.bot import Bot, VERSION
from pbjbt.models import Message, Command
from tests.common import _wrap, _get_log
from tests.common import *
import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

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

def test_bot_join_part(connected_bot, channels):
    fs = connected_bot.conn.conn
    j_msgz = [_wrap('JOIN {}'.format(i)) for i in channels]
    p_msgz = [_wrap('PART {}'.format(i)) for i in channels]
    with connected_bot.conn:
        connected_bot.join(MALFORMED_CHANNELS)
        for c in channels:
            assert c in connected_bot.channels
        for m in j_msgz:
            assert m in fs.sent
        connected_bot.part(MALFORMED_CHANNELS)
        for c in channels:
            assert c not in connected_bot.channels
        for m in p_msgz:
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

def test_run_join(response_bot, channels):
    fs = response_bot.conn.conn
    response_bot.join(MALFORMED_CHANNELS)
    response_bot.run()
    j_msgz = [_wrap('JOIN {}'.format(i)) for i in channels]
    for m in j_msgz:
        assert m in fs.sent

def test_handle(command_bot):
    fs = command_bot.conn.conn
    command_bot._activate_commands()
    inspired = fs.text.splitlines()
    for idx, i in enumerate(inspired):
        m = Message(i)
        command_bot.handle(m)
    command_bot.conn.conn = None
    for i in inspired:
        m = Message(i)
        assert not command_bot.handle(m)

def test_weird_callback(command_bot):
    def weird(message):
        return [None, None]
    command_bot.command('.*')(weird)
    command_bot._activate_commands()
    fs = command_bot.conn.conn
    inspired = fs.text.splitlines()
    for idx, i in enumerate(inspired):
        m = Message(i)
        assert not command_bot.handle(m)

def test_no_callback(command_bot):
    def no(message):
        pass
    command_bot.command('.*')(no)
    command_bot._activate_commands()
    fs = command_bot.conn.conn
    inspired = fs.text.splitlines()
    for idx, i in enumerate(inspired):
        m = Message(i)
        assert not command_bot.handle(m)

def test_builtin_join(connected_bot):
    log = ':foo!~somenick@irc.foo.bar.baz PRIVMSG #defaultchannel :.join newch'
    bad_log = ':foo!~somenick@irc.foo.bar.baz PRIVMSG #defaultchannel :.join'
    bad_reply = 'PRIVMSG #defaultchannel :Usage: .join #channelname'
    fs = connected_bot.conn.conn
    fs._set_reply_text(log)
    m = Message(log)
    assert not connected_bot.handle(m), 'Commands not yet activated!'
    with connected_bot.conn:
        # try out a proper command
        connected_bot._activate_commands()
        assert connected_bot.handle(m)
        assert _wrap('JOIN #newch') in fs.sent
        # try the case where the user doesn't provide an arg
        m = Message(bad_log)
        assert connected_bot.handle(m)
        assert _wrap(bad_reply) in fs.sent

def test_builtin_help(connected_bot):
    log = ':foo!~somenick@irc.foo.bar.baz PRIVMSG #defaultchannel :.help'
    fs = connected_bot.conn.conn
    fs._set_reply_text(log)
    m = Message(log)
    assert not connected_bot.handle(m), 'Commands not yet activated!'
    with connected_bot.conn:
        connected_bot._activate_commands()
        assert connected_bot.handle(m)

def test_builtin_ping(connected_bot):
    log = ':foo!~somenick@irc.foo.bar.baz PRIVMSG #defaultchannel :.ping'
    reply = 'PRIVMSG #defaultchannel :foo: pong'
    fs = connected_bot.conn.conn
    fs._set_reply_text(log)
    m = Message(log)
    assert not connected_bot.handle(m), 'Commands not yet activated!'
    with connected_bot.conn:
        connected_bot._activate_commands()
        assert connected_bot.handle(m)
        assert _wrap(reply) in fs.sent

def test_builtin_version(connected_bot):
    log = ':foo!~somenick@irc.foo.bar.baz PRIVMSG #defaultchannel :.version'
    reply = 'PRIVMSG #defaultchannel :foo: {} version {}'.format(NICK, VERSION)
    fs = connected_bot.conn.conn
    fs._set_reply_text(log)
    m = Message(log)
    assert not connected_bot.handle(m), 'Commands not yet activated!'
    with connected_bot.conn:
        connected_bot._activate_commands()
        assert connected_bot.handle(m)
        assert _wrap(reply) in fs.sent

def test_parse_args(mocked_bot):
    arg_sets = {
        '-n {0} --user-name {0} --real-name {0}'.format(NICK):
            lambda a: a.nick == a.username == a.realname == NICK,
        '-q': lambda a: a.quiet,
        '--port 13212 --network irc.some.place.net':
            lambda a: a.port == 13212 and a.network == 'irc.some.place.net',
        '-d -c': lambda a: a.debug and a.no_color,
    }
    for arguments, check in arg_sets.items():
        args = mocked_bot._parse_args(arguments=arguments.split(), override=False)
        assert check(args), 'Failed to parse {} correctly'.format(arguments)
    # test overrides
    xmas_tree = '-n {0} --user-name {0} --real-name {0} --port {1} --network {2}'.format(NICK, PORT, HOSTNAME)
    args = mocked_bot._parse_args(arguments=xmas_tree.split(), override=True)
    assert mocked_bot.conn.addr == HOSTNAME
    assert mocked_bot.conn.port == PORT
    assert mocked_bot.realname == NICK
    assert mocked_bot.username == NICK
    assert mocked_bot.nick == NICK