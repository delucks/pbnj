#!/usr/bin/env python3
'''simple examples of the library that just send text back to the channel
it came from'''
from pbjbt.bot import Bot

bot = Bot('hello')

@bot.command('^\.hello.*')  # regular expression
def helloworld(message):
    '''says hello world'''
    return '{0}: Hello world!'.format(message.nick)

match_shrugs = lambda m: m.type == 'ACTION' and m.message.startswith('shrug')
@bot.command(match_shrugs)  # using a callable, takes in a single pbjbt.models.Message object
def shrug(message):
    '''shrugs'''
    return '{}: ¯\_(ツ)_/¯'.format(message.nick)

if __name__ == '__main__':
    bot._parse_args(docstring=__doc__, override=True)
    bot.run()
