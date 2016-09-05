import pytest
from unittest.mock import patch
from pbjbt.connection import Connection
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
