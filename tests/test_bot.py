import pytest
from pbjbt.bot import Bot
from tests.common import _wrap, _get_log
from tests.common import *

def test_bot_init():
    b = Bot(NICK)
    assert NICK == b.username
    assert NICK == b.realname
    assert not b.conn, 'Connection was initialized'
    assert not b.commands, 'Command got inserted before run()'

@pytest.fixture
def mocked_bot():
    return Bot(NICK)
