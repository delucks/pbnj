#!/usr/bin/env python3
'''small bot that tallies up scores for strings that are incremented or
decremented in its channels and saves them to a sqlite database'''
from pbnj.bot import Bot
from pbnj import default_argparser
from collections import defaultdict
import sqlite3


def setup_db(path):
    db_connection = sqlite3.connect(path, isolation_level=None)
    cur = db_connection.cursor()
    cur.execute('create table if not exists Votes(Message varchar(70) not null, Up integer not null, Down integer not null)')
    return (db_connection, cur)


def vote_up(message, cursor):
    cursor.execute("select Up from Votes where Message = ?", (message, ))
    result = cursor.fetchone()
    if result:
        cursor.execute('update Votes set Up = Up + 1 where Message = ?', (message, ))
    else:
        cursor.execute('insert into Votes values(?, ?, ?)', (message, 1, 0))


def vote_down(message, cursor):
    cursor.execute('select Down from Votes where Message = ?', (message, ))
    result = cursor.fetchone()
    if result:
        cursor.execute('update Votes set Down = Down + 1 where Message = ?', (message, ))
    else:
        cursor.execute('insert into Votes values(?, ?, ?)', (message, 0, 1))


def summarize(message, cursor):
    cursor.execute('select Message, Up, Down from Votes where Message = ?', (message, ))
    result = cursor.fetchone()
    count_votes = result[1] + result[2]
    total = result[1] - result[2]
    percent_positive = round(result[1]/count_votes*100, 2)
    return 'voted {}: {} votes total, {}% positive'.format(
        total,
        count_votes,
        percent_positive
    )


def recognize_inc_expr(message):
    valid_exprs = ['--', '++']
    if message.type == 'PRIVMSG':
        for expr in valid_exprs:
            if expr in message.message:
                return True
    return False

b = Bot('tallybot')
DBFILE = 'tallies.sqlite3'
db, cursor = setup_db(DBFILE)


@b.command('^\.votes')
def votes(message):
    '''show current votes'''
    cursor.execute('select Message from Votes')
    for topic in cursor.fetchall():
        yield '{}: {}'.format(topic[0], summarize(topic[0], cursor))


@b.command(recognize_inc_expr)
def increment(message):
    '''tallies up score for a certain string'''
    valid_exprs = {'--': False, '++': True}
    topic = None
    for expr in valid_exprs:
        if expr in message.message:
            topic = message.message.split(expr)[0]
            if valid_exprs[expr]:
                vote_up(topic, cursor)
            else:
                vote_down(topic, cursor)
            break
    return '{}: {}'.format(topic, summarize(topic, cursor))

if __name__ == '__main__':
    default_argparser(override=b, docstring=__doc__)
    b.run()
    db.close()
