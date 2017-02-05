"""USAGE
    fanpy-archiver [options] <-|user> [<user> ...]

DESCRIPTION
    Archive statuses of users, sorted by date from oldest to newest, in
    the following format: <id> <date> <<screen_name>> <status_text>
    Date format is: YYYY-MM-DD HH:MM:SS TZ. Status <id> is used to
    resume archiving on next run. Archive file name is the user name.
    Provide "-" instead of users to read users from standard input.

OPTIONS
 -s --save-dir <path>   directory to save archives (default: current dir)
 -t --timeline <file>   archive own timeline into given file name
 -m --mentions <file>   archive own mentions into given file name
 -p --privatemsg <file> archive own private messages (both received and
                        sent) into given file name.
 -f --favorites         archive user's favorites instead of timeline
 -i --isoformat         store dates in ISO format (specifically RFC 3339)

AUTHENTICATION
    Authenticate to Fanfou using OAuth. OAuth authentication tokens are stored
    in ~/.fanfou_oauth.
"""
from __future__ import print_function, unicode_literals

import codecs
import datetime
import os
import sys
import time
from getopt import gnu_getopt, GetoptError

from .api import Fanfou, FanfouError
from .oauth import OAuth, read_token_file
from .oauth_dance import oauth_dance
from .util import Fail


# Registered by mookrs
CONSUMER_KEY = '1469b495a824c7abb2bf9fd2c75930e8'
CONSUMER_SECRET = '9095f46ecf5ede903fa79a57263fd153'


def parse_args(args, options):
    """Parse arguments from command-line to set options."""
    short_opts = 's:t:m:fp:ih'
    long_opts = ['save-dir=', 'timeline=', 'mentions=',
                 'favorites', 'privatemsg=', 'isoformat', 'help']
    opts, extra_args = gnu_getopt(args, short_opts, long_opts)

    for opt, arg in opts:
        if opt in ('-s', '--save-dir'):
            options['save-dir'] = arg
        elif opt in ('-t', '--timeline'):
            options['timeline'] = arg
        elif opt in ('-m', '--mentions'):
            options['mentions'] = arg
        elif opt in ('-f', '--favorites'):
            options['favorites'] = True
        elif opt in ('-p', '--privatemsg'):
            options['privatemsg'] = arg
        elif opt in ('-i', '--isoformat'):
            options['isoformat'] = True
        elif opt in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)

    options['extra_args'] = extra_args


def save_statuses(filename, statuses):
    """Save statuses from list to file.

    Save statuses from list to file, one per line:
        <status id> <date> <<user>> <text>

    :param filename: A string representing the file name to save statuses to
    :param statuses: A status text list
    """
    if not statuses:
        return

    try:
        archive = codecs.open(filename, 'w', encoding='utf-8')
        for s in reversed(statuses):
            archive.write('{}\n'.format(s))
    except IOError as e:
        print('Cannot save statuses: {}'.format(e))
        return
    else:
        archive.close()


def format_date(created_at, isoformat=False):
    """Parse Fanfou's UTC date."""
    t = time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
    timezones = time.timezone if not time.daylight else time.altzone
    dt = datetime.datetime(*t[:-3]) - datetime.timedelta(seconds=timezones)
    t = dt.timetuple()
    if isoformat:
        return dt.isoformat()
    else:
        return time.strftime('%Y-%m-%d %H:%M:%S %Z', t)


def format_text(text):
    """Transform special chars in text to have only one line."""
    return text.replace('\n', '\\n').replace('\r', '\\r')


def get_statuses_portion(fanfou, user_id, max_id=None, mentions=None, received_privatemsg=None,
                         favorites=False, isoformat=False):
    """Get a portion of the statuses of a screen name."""
    kwargs = dict(id=user_id, count=60, mode='lite')
    if max_id:
        kwargs['max_id'] = max_id

    statuses = []
    if mentions:
        status_list = fanfou.statuses.mentions(**kwargs)
    elif received_privatemsg is not None:
        if received_privatemsg:
            status_list = fanfou.direct_messages.inbox(**kwargs)
        else:
            status_list = fanfou.direct_messages.sent(**kwargs)
    elif favorites:
        status_list = fanfou.favorites(**kwargs)
    else:
        status_list = fanfou.statuses.user_timeline(**kwargs)

    for s in status_list:
        text = s['text']
        max_id = s['id']
        if received_privatemsg is None:
            statuses.append(
                '{} {} <{}> {}'.format(
                    max_id,
                    format_date(s['created_at'], isoformat=isoformat),
                    s['user']['screen_name'],
                    format_text(text)))
        else:
            statuses.append(
                '{} {} <{}> @{} {}'.format(
                    max_id,
                    format_date(s['created_at'], isoformat=isoformat),
                    s['sender_screen_name'],
                    s['recipient_screen_name'],
                    format_text(text)))
    return statuses, max_id


def get_statuses(fanfou, user_id, mentions=None, received_privatemsg=None,
                 favorites=False, isoformat=False):
    """Get all the statuses for a user id."""
    statuses = []
    max_id = None
    fail = Fail()

    while True:
        try:
            portion, max_id = get_statuses_portion(
                fanfou, user_id, max_id, mentions, received_privatemsg, favorites, isoformat)
        except FanfouError as e:
            if e.e.code == 401:
                print('Fail: {} Unauthorized (statuses of that user are protected)'.format(
                    e.e.code))
                break
            elif e.e.code == 404:
                print('Fail: {} This profile does not exist'.format(e.e.code))
                break
            else:
                print('Fail: {}\nRetrying...'.format(e[:500]))
            fail.wait(3)
        except KeyError as e:
            print('Fail: KeyError {} - Retrying...'.format(e))
            fail.wait(3)
        except KeyboardInterrupt:
            print('\n[Keyboard Interrupt]', file=sys.stderr)
            sys.exit(1)
        else:
            statuses.extend(portion)
            num = len(portion)
            if (num == 0) or (favorites and num < 60):
                break
            print('Browsing {} statuses ({})'.format(user_id if user_id else 'home', num))
            fail = Fail()

    return statuses


def main(args=sys.argv[1:]):
    options = {
        'save-dir': '.',
        'timeline': '',
        'mentions': '',
        'privatemsg': '',
        'favorites': False,
        'isoformat': False,
    }
    try:
        parse_args(args, options)
    except GetoptError as e:
        print("I can't do that, {}.".format(e), file=sys.stderr)
        sys.exit(1)

    if (not options['extra_args'] and
        not (options['timeline'] or options['mentions'] or options['privatemsg'])):
        print(__doc__)
        sys.exit(1)

    oauth_filename = os.environ.get('HOME', os.environ.get('USERPROFILE', '')) + os.sep + '.fanfou_oauth'
    if not os.path.exists(oauth_filename):
        oauth_dance('Fanfou-Archiver', CONSUMER_KEY, CONSUMER_SECRET, oauth_filename)
    oauth_token, oauth_token_secret = read_token_file(oauth_filename)
    fanfou = Fanfou(auth=OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

    if options['timeline']:
        filename = options['save-dir'] + os.sep + options['timeline']
        print('* Archiving own timeline in {}'.format(filename))

        statuses = get_statuses(fanfou, user_id='', isoformat=options['isoformat'])

        save_statuses(filename, statuses)
        print('Total statuses in own timeline: {}'.format(len(statuses)))

    if options['mentions']:
        filename = options['save-dir'] + os.sep + options['mentions']
        print('* Archiving own mentions in {}'.format(filename))

        statuses = get_statuses(fanfou, user_id='', mentions=options['mentions'],
                                isoformat=options['isoformat'])

        save_statuses(filename, statuses)
        print('Total mentions: {}'.format(len(statuses)))

    if options['privatemsg']:
        filename = options['save-dir'] + os.sep + options['privatemsg']
        print('* Archiving own private messages in {}'.format(filename))

        msg_received = get_statuses(fanfou, user_id='', received_privatemsg=True,
                                    isoformat=options['isoformat'])
        msg_sent = get_statuses(fanfou, user_id='', received_privatemsg=False,
                                isoformat=options['isoformat'])
        msg = msg_received + msg_sent

        save_statuses(filename, msg)
        print('Total private messages received and sent: {}'.format(len(msg)))

    # Read users from command-line or stdin
    users = options['extra_args']
    if len(users) == 1 and users[0] == '-':
        users = [line.strip() for line in sys.stdin.readlines() if line.strip()]
    total = 0
    for user in users:
        filename = options['save-dir'] + os.sep + user
        if options['favorites']:
            filename = filename + '-favorites'
        print('* Archiving {} statuses in {}'.format(user, filename))

        statuses = get_statuses(fanfou, user, favorites=options['favorites'],
                                isoformat=options['isoformat'])

        save_statuses(filename, statuses)
        total += len(statuses)
        print('Total statuses for {}: {}'.format(user, len(statuses)))

    if users:
        print('Total: {} statuses for {} users'.format(total, len(users)))


if __name__ == '__main__':
    main()
