import re
import types
import pytest
from tests.common import _wrap, _get_log
from tests.common import *
import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

from pbjbt.models import Message, Command, _builtin_command

def test_message_types():
    priv = ':delucks!~delucks@localhost.localdomain PRIVMSG #channel :hello'
    action = ':delucks!~delucks@localhost.localdomain PRIVMSG #channel :ACTION something'
    server = ':irc.example.net 366 foo #channel :End of NAMES list'
    privmsg = Message(priv)
    servermsg = Message(server)
    actionmsg = Message(action)
    # privmsg
    assert privmsg.type == 'PRIVMSG'
    assert str(privmsg) == privmsg.message
    assert repr(privmsg) == priv
    assert privmsg.host
    assert privmsg.nick
    assert privmsg.realname
    assert privmsg.dest
    assert privmsg.message
    # server message
    assert servermsg.type == 366
    assert str(servermsg) == server
    assert repr(servermsg) == server
    # action message
    assert actionmsg.type == 'ACTION'
    assert str(actionmsg) == actionmsg.message
    assert repr(actionmsg) == action
    assert actionmsg.host
    assert actionmsg.nick
    assert actionmsg.realname
    assert actionmsg.dest
    assert actionmsg.message
    # comparison
    privmsg_again = Message(priv)
    assert privmsg != servermsg, '__eq__ method of Message is broken'
    assert privmsg != actionmsg, '__eq__ method of Message is broken'
    assert privmsg == privmsg_again, '__eq__ method of Message is broken'
    assert servermsg != privmsg_again, '__eq__ method of Message is broken'
    assert servermsg != actionmsg, '__eq__ method of Message is broken'
    # a malformed hostmask will execute "regex fucked up" codepath
    malformed_hm = ':invalid@localhost.localdomain PRIVMSG #channel :something'
    with pytest.raises(AttributeError):
        malformed = Message(malformed_hm)

def test_command(privmsg):
    filter_lambda = lambda m: m.type == 'PRIVMSG' and 'hello' in m.message
    filter_regex = '^\.test_cmd'
    docz = '''test documentation'''
    def callback_generator(message):
        __doc__ = docz 
        for item in message.message.split():
            yield item
    def callback_string(message):
        __doc__ = docz 
        return message.message
    c0 = Command(filter_lambda, callback_generator)
    c1 = Command(filter_lambda, callback_string)
    c2 = Command(filter_regex, callback_generator)
    c3 = Command(filter_regex, callback_string)
    for i in [c0, c1, c2, c3]:
        assert i
        assert repr(i) == i.name
        if i.__doc__:
            assert str(i) == i.__doc__
        else:
            assert str(i) == 'This triggers it: {}'.format(i.filterspec)
        if callable(i.filterspec):
            assert i.match(privmsg) == i.filterspec(privmsg)
        else:
            assert i.match(privmsg) == re.match(i.filterspec, privmsg.message)
    # check return types
    assert isinstance(c0(privmsg), types.GeneratorType)
    assert isinstance(c1(privmsg), str)
    assert isinstance(c2(privmsg), types.GeneratorType)
    assert isinstance(c3(privmsg), str)
    # test __eq__
    assert c0 != c1
    assert c0 != c2
    assert c0 != c3
    assert c1 != c2
    assert c1 != c3
    assert c2 != c3
    c0_again = Command(filter_lambda, callback_generator)
    assert c0 == c0_again
