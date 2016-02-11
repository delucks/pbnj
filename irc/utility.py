import inspect
import sys
import re
import logging
log = logging.getLogger()


def wrap_command(func, cmd_regex, arg_handling):
    ''' Decorator to match a regular expression against messages
    then modify the arguments to the decorated function to pull out
    different properties of the message.
    The last argument will always be filled in by the macro
    The regex and handling stragegy get read by the macro and stay static
    The checks in the beginning which return False are for early termination of
    the method before we hit any expensive code paths (regex'ing the message)
    '''
    def wrapped(*args):
        # we don't need to pass args[0] ever because it's already bound to 'self'
        msg_object = args[1]
        log.debug('wrapped {1} with args {0}'.format(args, func.__name__))
        # commands only apply to private/public messages and /me
        if msg_object['type'] == 'PRIVMSG' or msg_object['type'] == 'ACTION':
            message = msg_object['message']
            match = re.match(cmd_regex, message)
            if not match:
                log.debug('{0} failed to match {1}'.format(
                    func.__name__, message)
                )
                return False
            if arg_handling == 'group':
                newargs = (args[1], match.groups())
            elif arg_handling == 'first':
                newargs = (args[1], message.split()[1])
            elif arg_handling == 'pass':
                newargs = (args[1], message.split()[1:])
            else:  # none
                log.debug('{0} uses none, so I am passing it {1}'.format(func.__name__, args))
                newargs = args[1:]
            log.debug('wrap_command calling {0} with {1}'.format(
                func.__name__, newargs)
            )
            func(*newargs)
        else:
            return False
    wrapped.__doc__ = func.__doc__
    return wrapped


def bot_command(cmd_regex, arg_handling):
    ''' marks a method as a command within a subclass of IRCBot.
    It can then interact with incoming irc messages after the
    class is activated with @active_bot()
    '''
    def command_decorator(func):
        func._cmd = True
        func._cmd_regex = cmd_regex
        func._arg_handling = arg_handling
        return func
    return command_decorator
