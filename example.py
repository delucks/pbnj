#!/usr/bin/env python3
'''a simple example of the pbjbt library'''
from pbjbt.bot import Bot

bot = Bot('hello')

@bot.command('^\.hello.*')  # regular expression
def helloworld(message):
    '''says hello world'''
    return '{0}: Hello world!'.format(message.nick)

match_shrugs = lambda m: m.type == 'ACTION' and m.message.startswith('shrug')

@bot.command(match_shrugs)  # callable, takes in a single pbjbt.Message object
def shrug(message):
    '''shrugs'''
    return '{}: ¯\_(ツ)_/¯'.format(message.nick)

if __name__ == '__main__':
    args = bot._parse_args(__doc__, override=True)
    bot.join(['#foobar'])
    bot.run()
