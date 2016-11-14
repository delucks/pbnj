#!/usr/bin/env python3
'''simple examples of the library that just send text back to the channel
it came from'''
from pbnj.bot import Bot
from pbnj import default_argparser

bot = Bot('hello')

@bot.command('^\.hello.*')  # regular expression
def helloworld(message):
    '''says hello world'''
    return '{0}: Hello world!'.format(message.nick)

if __name__ == '__main__':
    default_argparser(override=bot, docstring=__doc__)
    bot.run()
