import re
import logging

log = logging.getLogger("pbnj")

attr_filter = lambda x: {
    a: getattr(x, a) for a in dir(x) if not "__" in a and not callable(getattr(x, a))
}


class Message:
    """object to get passed between Bot class and its command methods. Separates
    the logic of parsing a string from the socket into more actionable objects
    """

    def __init__(self, raw_msg):
        self.raw_msg = raw_msg
        self.message = None
        self.parse()

    def __str__(self):
        return self.message or self.raw_msg

    def __repr__(self):
        return self.raw_msg

    def __eq__(self, other):
        self_attr = attr_filter(self)
        for item, val in self_attr.items():
            if val != getattr(other, item, False):
                return False
        return True

    def parse(self):
        """ Parse the message
        TODO handle all the numeric ones
        TODO remove dependence on regular expressions
        """
        sp = self.raw_msg.split()
        host = sp[0]
        if "@" in host:
            hostmask = host[1:] if host.startswith(":") else host
            re_matches = re.match(
                "^([a-zA-Z0-9_\-]+)!~?([a-zA-Z0-9\ ]+)@(.*)", hostmask
            )
            try:
                re_groups = re_matches.groups()
                self.nick = re_groups[0]
                self.realname = re_groups[1]
                self.host = re_groups[2]
            except Exception as e:
                log.error("The regex fucked up! On this input for the hostmask")
                log.error(hostmask)
                raise
            self.type = sp[1]
        else:
            # this is a server directly sending us something
            self.host = host
            code = sp[1]
            self.type = int(code) if code.isdigit() else code
        if self.type == "PRIVMSG":
            self.dest = sp[2]
            if "#" in self.dest:
                self.reply_dest = self.dest
            else:
                self.reply_dest = self.nick
            m = " ".join(sp[3:])
            msg = m[1:] if m.startswith(":") else m
            if msg.startswith("ACTION"):
                self.type = "ACTION"
                msg = msg[7:]  # actions are privmsgs, why
            self.message = msg
            self.args = msg.split()[1:]


class _builtin_command:
    """lightweight decorator for doing the marking of builtin commands as such
    before runtime. This is necessarily outside of the Bot class because this
    needs to mark methods of that class as loadable before the class' __init__
    is called"""

    def __init__(self, filterspec):
        self.filterspec = filterspec

    def __call__(self, f):
        def wrapped_f(*args):
            return f(*args)

        wrapped_f._command = True
        wrapped_f._filterspec = self.filterspec
        wrapped_f.__name__ = f.__name__
        wrapped_f.__doc__ = f.__doc__
        return wrapped_f


class Command:
    """holds the message filtering specification of a command registered with
    the bot (a callable or string regex) as well as the callback to hit if a
    message is matched"""

    def __init__(self, filterspec, callback):
        if not (callable(filterspec) or isinstance(filterspec, str)):
            raise ValueError(
                "filterspec arg for Command classes must be callable or a string (valid regex)!"
            )
        self.filterspec = filterspec
        self.callback = callback
        self.name = callback.__name__
        self.__doc__ = callback.__doc__

    def __str__(self):
        return self.__doc__ or "This triggers it: {}".format(self.filterspec)

    def __repr__(self):
        return self.name

    def __call__(self, *args):
        return self.callback(*args)

    def __eq__(self, other):
        return (
            self.filterspec == other.filterspec
            and self.callback == other.callback
            and self.name == other.name
            and self.__doc__ == other.__doc__
        )

    def match(self, message):
        """try to match an incoming message (quickly) return something falsey if
        not"""
        if callable(self.filterspec):
            return self.filterspec(message)
        else:
            """we only support the naive regex format for privmsg types"""
            if message.type == "PRIVMSG":
                log.debug(
                    "Trying to match {} with {}".format(
                        message.message, self.filterspec
                    )
                )
                return re.match(self.filterspec, message.message)
            return None
