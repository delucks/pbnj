# -*- coding: utf-8 -*-
import inspect
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
        msg_object = args[1]
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
                newargs = (args[0], args[1], match.groups())
            elif arg_handling == 'first':
                newargs = (args[0], args[1], message.split()[1])
            elif arg_handling == 'pass':
                newargs = (args[0], args[1], message.split()[1:])
            else:  # none
                newargs = args
            log.debug('wrap_command calling {0} with {1}'.format(
                func.__name__, newargs)
            )
            func(*newargs)
        else:
            return False
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


def active_bot():
    ''' marks a subclass of IRCBot as the active bot to use.
    Activates all of the @bot_command(...) commands by decorating
    them with wrap_command(...)
    '''
    def wrap_bot_class(bot_class):
        for m_name, method in inspect.getmembers(bot_class, inspect.ismethod):
            if '_cmd' in dir(method):  # this is SO HACKY
                # this is a command method, and needs to be decorated
                wrapped = wrap_command(
                    method, method._cmd_regex, method._arg_handling
                )
                bot_class.commands[m_name] = wrapped
                # we're manually decorating because fuck you iteration
                setattr(bot_class, m_name, wrapped)
        return bot_class
    return wrap_bot_class
