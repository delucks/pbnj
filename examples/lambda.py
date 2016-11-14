#!/usr/bin/env python3
'''shrugbot here shows us how to use a lambda as a command filter, as well as
how to work with ACTION (/me) messages'''
from pbnj.bot import Bot
from pbnj import default_argparser

bot = Bot('meh')

# the callable gets a single pbnj.models.Message object
match_shrugs = lambda m: m.type == 'ACTION' and m.message.startswith('shrug')
@bot.command(match_shrugs)
def shrug(message):
    '''shrugs'''
    return '{}: ¯\_(ツ)_/¯'.format(message.nick)

if __name__ == '__main__':
    default_argparser(override=bot, docstring=__doc__)
    bot.run()
