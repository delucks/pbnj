NICK = 'foo'
CHANNEL = '#foo'
USER = 'bar'
REALNAME = 'baz'
HOSTNAME = 'localhost'
PORT = 6667


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

def _wrap(message):
    '''as if it was sent/recieved over a socket'''
    return bytes('{}\r\n'.format(message).encode('utf-8'))

def _get_log(logname):
    import os
    pwd = os.path.dirname(os.path.realpath(__file__))
    logs_dir = os.path.join(pwd, 'logs/')
    log_path = os.path.join(logs_dir, logname)
    with open(log_path) as f:
        return f.read()
