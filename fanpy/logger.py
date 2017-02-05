"""
fanpy-log - Fanfou Logger

USAGE:

    fanpy-log <user_id>

DESCRIPTION:

    Produce a complete archive in text form of a user's statuses. The
    archive format is:

        screen_name <status_id>
        Date: <status_time>
        [In-Reply-To: a_status_id]
        [Repost: a_status_id]

            Status text possibly spanning multiple lines with
            each line indented by four spaces.


    Each status is separated by two blank lines.

"""

from __future__ import print_function, unicode_literals

import os
import sys
from time import sleep
try:
    import HTMLParser
except ImportError:
    import html.parser as HTMLParser

from .api import Fanfou, FanfouError
from .oauth import OAuth, read_token_file
from .oauth_dance import oauth_dance
from .util import print_nicely

# Registered by mookrs
CONSUMER_KEY = '1469b495a824c7abb2bf9fd2c75930e8'
CONSUMER_SECRET = '9095f46ecf5ede903fa79a57263fd153'
OAUTH_FILENAME = os.environ.get('HOME', os.environ.get('USERPROFILE', '')) + os.sep + '.fanfou_oauth'
html_parser = HTMLParser.HTMLParser()


def log_debug(msg):
    print(msg, file=sys.stderr)


def get_statuses(fanfou, user_id, max_id=None):
    kwargs = dict(id=user_id, count=60, mode='lite')
    if max_id:
        kwargs['max_id'] = max_id
    n_statuses = 0
    statuses = fanfou.statuses.user_timeline(**kwargs)
    for status in statuses:
        print('{} {}\nDate: {}'.format(status['user']['screen_name'],
                                       status['id'],
                                       status['created_at']))
        if status.get('in_reply_to_status_id'):
            print('In-Reply-To: {}'.format(status['in_reply_to_status_id']))
        elif status.get('repost_status_id'):
            print('Repost: {}'.format(status['repost_status_id']))
        print()
        for line in html_parser.unescape(status['text']).splitlines():
            print_nicely('    ' + line)
        print()
        print()
        max_id = status['id']
        n_statuses += 1
    return n_statuses, max_id


def main(args=sys.argv[1:]):
    if not args:
        print(__doc__)
        sys.exit(1)

    if not os.path.exists(OAUTH_FILENAME):
        oauth_dance('The Python Fanfou Logger', CONSUMER_KEY, CONSUMER_SECRET, OAUTH_FILENAME)

    oauth_token, oauth_token_secret = read_token_file(OAUTH_FILENAME)
    fanfou = Fanfou(auth=OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

    user_id = args[0]
    max_id = args[1] if args[1:] else None
    n_statuses = 0
    while True:
        try:
            statuses_processed, max_id = get_statuses(fanfou, user_id, max_id)
            n_statuses += statuses_processed
            log_debug('Processed {} statuses (max_id {})'.format(n_statuses, max_id))
            if statuses_processed == 0:
                log_debug("That's it, we got all the statuses we could. Done.")
                break
        except FanfouError as e:
            log_debug("Fanfou bailed out. I'm going to sleep a bit then try again.")
            sleep(3)

if __name__ == '__main__':
    main()
