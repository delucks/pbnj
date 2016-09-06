#!/usr/bin/env python3
'''tallies up score for a certain string'''
from pbjbt.bot import Bot
from collections import defaultdict

'''this shows how to set up a custom prefix for builtin commands- $help will be
recognized by this bot now, as an example'''
b = Bot('tally', builtin_prefix='^\$')

all_votes = defaultdict(list)
summarize = lambda v: 'voted {}: {} votes total, {}% positive'.format(
    sum(v),
    len(v),
    round(len([i for i in v if i > 0])/len(v)*100, 2)
)

@b.command('^\$votes')
def votes(message):
    '''show current votes'''
    for topic in all_votes:
        yield '{}: {}'.format(topic, summarize(all_votes[topic]))

def recognize_inc_expr(message):
    valid_exprs = ['--', '++']
    if message.type == 'PRIVMSG':
        for expr in valid_exprs:
            if expr in message.message:
                return True
    return False

@b.command(recognize_inc_expr)
def increment(message):
    '''tallies up score for a certain string'''
    valid_exprs = {'--': -1, '++': 1}
    topic = None
    for expr in valid_exprs:
        if expr in message.message:
            topic = message.message.split(expr)[0]
            all_votes[topic].append(valid_exprs[expr])
    if sum(all_votes[topic]) > b.max_msg_len:
        all_votes[topic] = []
        return 'You flew too close too the sun. Enthusiastic voting though!'
    else:
        return '{}: {}'.format(topic, summarize(all_votes[topic]))

if __name__ == '__main__':
    b._parse_args(override=True)
    b.run()
