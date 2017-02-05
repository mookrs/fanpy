# -*- coding: utf-8 -*-
"""
USAGE:

 fanpy [action] [options]


ACTIONS:
 authorize      authorize the command-line tool to interact with Fanfou
 follow         follow a user
 friends        get latest statuses from your friends (default action)
 help           print this help text that you are currently reading
 leave          stop following a user
 replies        get latest replies to you
 search         search fanfou (Beware: octothorpe, escape it)
 set            set your fanfou status
 repl           begin a read-eval-print loops with a configured fanfou
                    object

OPTIONS:

 -r --refresh               run this command forever, polling every once
                            in a while (default: every 5 minutes)
 -R --refresh-rate <rate>   set the refresh rate (in seconds)
 -f --format <format>       specify the output format for status updates
 -c --config <filename>     read options from given config file
                            (default ~/.fanfou)
 -l --length <count>        specify number of status updates shown
                            (default: 20, max: 60)
 -t --timestamp             show time before status lines
 -d --datestamp             show date before status lines
    --oauth <filename>      filename to read/store oauth credentials

FORMATS for the --format option

 default         one line per status
 verbose         multiple lines per status, more verbose status info
 json            raw json data from the api on each line
 urls            nothing but URLs
 ansi            ansi color (rainbow mode)


CONFIG FILES

 The config file should be placed in your home directory and be named .fanfou.
 It must contain a [fanfou] header, and all the desired options you wish to
 set, like so:

[fanfou]
format: <desired_default_format_for_output>
timestamp: true

 OAuth authentication tokens are stored in the file `.fanfou_oauth` in your
 home directory.
"""

from __future__ import print_function, unicode_literals

try:
    input = raw_input
except NameError:
    pass

import code
import datetime
from getopt import gnu_getopt, GetoptError
import json
import locale
import os.path
import re
import sys
import time

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser
try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote
try:
    import HTMLParser
except ImportError:
    import html.parser as HTMLParser

from . import ansi
from .api import Fanfou, FanfouError
from .oauth import OAuth, read_token_file
from .oauth_dance import oauth_dance
from .util import print_nicely

# Registered by mookrs
CONSUMER_KEY = '1469b495a824c7abb2bf9fd2c75930e8'
CONSUMER_SECRET = '9095f46ecf5ede903fa79a57263fd153'

OPTIONS = {
    'action': 'friends',
    'refresh': False,
    'refresh-rate': 300,
    'format': 'default',
    'length': 20,
    'timestamp': False,
    'datestamp': False,
    'config-filename': os.environ.get('HOME', os.environ.get('USERPROFILE', '')) +
                       os.sep + '.fanfou',
    'oauth-filename': os.environ.get('HOME', os.environ.get('USERPROFILE', '')) +
                      os.sep + '.fanfou_oauth',
    'extra-args': [],
    'invert-split': False,
    'force-ansi': False,
}

html_parser = HTMLParser.HTMLParser()
hashtag_re = re.compile(r'(?P<hashtag>#\S+#)')
profile_re = re.compile(r'(?P<profile>\@\S+)')


def parse_args(args):
    options = {}

    short_opts = 'rR:f:l:tdc:h'
    long_opts = ['refresh', 'refresh-rate=',
                 'format=', 'length=', 'timestamp', 'datestamp',
                 'config=', 'oauth=', 'help', 'invert-split', 'force-ansi']
    opts, extra_args = gnu_getopt(args, short_opts, long_opts)
    # decode Non-ASCII args for Python 2
    if extra_args and hasattr(extra_args[0], 'decode'):
        extra_args = [arg.decode(locale.getpreferredencoding()) for arg in extra_args]

    for opt, arg in opts:
        if opt in ('-r', '--refresh'):
            options['refresh'] = True
        elif opt in ('-R', '--refresh-rate'):
            options['refresh-rate'] = int(arg)
        elif opt in ('-f', '--format'):
            options['format'] = arg
        elif opt in ('-l', '--length'):
            options['length'] = int(arg)
        elif opt in ('-t', '--timestamp'):
            options['timestamp'] = True
        elif opt in ('-d', '--datestamp'):
            options['datestamp'] = True
        elif opt in ('-c', '--config'):
            options['config-filename'] = arg
        elif opt == '--oauth':
            options['oauth-filename'] = arg
        elif opt in ('-h', '--help'):
            options['action'] = 'help'
        elif opt == '--invert-split':
            options['invert-split'] = True
        elif opt == '--force-ansi':
            options['force-ansi'] = True

    if extra_args and 'action' not in options:
        options['action'] = extra_args[0]
    options['extra-args'] = extra_args[1:]

    return options


def load_config(filename):
    options = {}
    if os.path.exists(filename):
        cp = ConfigParser()
        cp.read(filename)
        if cp.has_section('fanfou'):
            for key in cp['fanfou']:
                if key in ('refresh', 'timestamp', 'datestamp', 'invert-split', 'force-ansi'):
                    options[key] = cp.getboolean('fanfou', key)
                elif key in ('refresh-rate', 'length'):
                    options[key] = cp.getint('fanfou', key)
                elif key in ('format', 'config-filename', 'oauth-filename', 'action'):
                    options[key] = cp.get('fanfou', key)
    return options


def get_time_string(created_at, options, format='%a %b %d %H:%M:%S +0000 %Y'):
    is_timestamp = options['timestamp']
    is_datestamp = options['datestamp']
    t = time.strptime(created_at, format)
    timezones = time.timezone if not time.daylight else time.altzone
    dt = datetime.datetime(*t[:-3]) - datetime.timedelta(seconds=timezones)
    t = dt.timetuple()
    if is_timestamp and is_datestamp:
        return time.strftime('%Y-%m-%d %H:%M:%S ', t)
    elif is_timestamp:
        return time.strftime('%H:%M:%S ', t)
    elif is_datestamp:
        return time.strftime('%Y-%m-%d ', t)
    return ''


class StatusFormatter(object):
    def __call__(self, status, options):
        return '{}@{} {}'.format(
            get_time_string(status['created_at'], options),
            status['user']['screen_name'],
            html_parser.unescape(status['text']))


class VerboseStatusFormatter(object):
    def __call__(self, status, options):
        return '-- {} on {}\n{}\n'.format(
            status['user']['screen_name'],
            status['created_at'],
            html_parser.unescape(status['text']))


class JSONStatusFormatter(object):
    def __call__(self, status, options):
        status['text'] = html_parser.unescape(status['text'])
        return json.dumps(status)


class URLStatusFormatter(object):
    def __call__(self, status, options):
        url_re = re.compile(r'https?://\S+')
        urls = url_re.findall(status['text'])
        return '\n'.join(urls) if urls else ''


class AnsiStatusFormatter(object):
    def __init__(self):
        self.color_map = ansi.ColorMap()

    def __call__(self, status, options):
        color = self.color_map.color_for(status['user']['screen_name'])
        return '{}{}{}{} {} '.format(
            get_time_string(status['created_at'], options),
            ansi_formatter.cmd_color(color),
            status['user']['screen_name'],
            ansi_formatter.cmd_reset(),
            self.replace_in_status(status['text']))

    def replace_in_status(self, status):
        txt = html_parser.unescape(status)
        txt = re.sub(hashtag_re, self.repl, txt)
        txt = re.sub(profile_re, self.repl, txt)
        return txt

    def repl(self, match):
        ansi_types = {
            'clear': ansi_formatter.cmd_reset(),
            'hashtag': ansi_formatter.cmd_bold(),
            'profile': ansi_formatter.cmd_underline(),
        }

        s = None
        try:
            key = match.lastgroup
            if match.group(key):
                s = '{}{}{}'.format(ansi_types[key], match.group(key), ansi_types['clear'])
        except IndexError:
            pass
        return s


class AdminFormatter(object):
    def __call__(self, action, user):
        user_str = '{} ({})'.format(user['screen_name'], user['id'])
        if action == 'follow':
            return 'You are now following {}.\n'.format(user_str)
        else:
            return 'You are no longer following {}.\n'.format(user_str)


class VerboseAdminFormatter(object):
    def __call__(self, action, user):
        return('-- {}: {} ({})'.format(
            'Following' if action == 'follow' else 'Leaving',
            user['screen_name'],
            user['id']))


class JSONAdminFormatter(object):
    def __call__(self, action, user):
        return json.dumps(user)


formatters = {}
status_formatters = {
    'default': StatusFormatter,
    'verbose': VerboseStatusFormatter,
    'json': JSONStatusFormatter,
    'urls': URLStatusFormatter,
    'ansi': AnsiStatusFormatter
}
formatters['status'] = status_formatters

admin_formatters = {
    'default': AdminFormatter,
    'verbose': VerboseAdminFormatter,
    'json': JSONAdminFormatter,
    'urls': AdminFormatter,
    'ansi': AdminFormatter
}
formatters['admin'] = admin_formatters

formatters['search'] = status_formatters


def get_formatter(action_type, options):
    formatters_dict = formatters.get(action_type)
    if not formatters_dict:
        raise FanfouError(
            'There was an error finding a class of formatters for your type ({})'.format(
                action_type))
    f = formatters_dict.get(options['format'])
    if not f:
        raise FanfouError(
            "Unknown formatter '{}' for {} action".format(options['format'], action_type))
    return f()


class Action(object):
    def ask(self, subject='perform this action', careful=False):
        """Requests from the user using `input` if `subject` should be
        performed. When `careful`, the default answer is NO, otherwise YES.
        Returns the user answer in the form `True` or `False`.
        """
        sample = '(y/N)' if careful else '(Y/n)'
        prompt = 'You really want to {} {}? '.format(subject, sample)
        try:
            answer = input(prompt).lower()
            if careful:
                return answer in ('yes', 'y')
            else:
                return answer not in ('no', 'n')
        except EOFError:
            print(file=sys.stderr)
            default = False if careful else True
            return default

    def __call__(self, fanfou, options):
        action = ACTIONS.get(options['action'], NoSuchAction)()
        try:
            do_action = lambda: action(fanfou, options)
            if options['refresh']:
                while True:
                    do_action()
                    sys.stdout.flush()
                    time.sleep(options['refresh-rate'])
            else:
                do_action()
        except KeyboardInterrupt:
            print('\n[Keyboard Interrupt]', file=sys.stderr)


class NoSuchActionError(Exception):
    pass


class NoSuchAction(Action):
    def __call__(self, fanfou, options):
        raise NoSuchActionError('No such action: {}'.format(options['action']))


class DoNothingAction(Action):
    def __call__(self, fanfou, options):
        pass


class StatusAction(Action):
    def __call__(self, fanfou, options):
        statuses = self.get_statuses(fanfou, options)
        fmt = get_formatter('status', options)
        for status in statuses:
            status = fmt(status, options)
            if status.strip():
                print_nicely(status)


class FriendsAction(StatusAction):
    def get_statuses(self, fanfou, options):
        return reversed(fanfou.statuses.home_timeline(count=options['length']))


class RepliesAction(StatusAction):
    def get_statuses(self, fanfou, options):
        return reversed(fanfou.statuses.mentions(count=options['length']))


class AdminAction(Action):
    def __call__(self, fanfou, options):
        if not (options['extra-args'] and options['extra-args'][0]):
            raise FanfouError('You need to specify a user (user_id)')
        fmt = get_formatter('admin', options)
        try:
            user = self.get_user(fanfou, options['extra-args'][0])
        except FanfouError as e:
            print('There was a problem following or leaving the specified user.')
            print('- You may be trying to follow a user you are already following;')
            print('- Leaving a user you are not currently following;')
            print('- Or the user may not exist.')
            print()
            print(e)
        else:
            print_nicely(fmt(options['action'], user))


class FollowAction(AdminAction):
    def get_user(self, fanfou, user_id):
        return fanfou.friendships.create(_id=user_id)


class LeaveAction(AdminAction):
    def get_user(self, fanfou, user_id):
        return fanfou.friendships.destroy(_id=user_id)


class SearchAction(Action):
    def __call__(self, fanfou, options):
        try:
            query_string = '+'.join(map(quote, options['extra-args']))
        except KeyError:
            # Python 2 thorws KeyError
            query_string = '+'.join([quote(term.encode(locale.getpreferredencoding()))
                for term in options['extra-args']])

        results = fanfou.search.public_timeline(q=query_string)
        fmt = get_formatter('search', options)
        for result in results:
            result = fmt(result, options)
            if result.strip():
                print_nicely(result)


class SetStatusAction(Action):
    def __call__(self, fanfou, options):
        status_text = ' '.join(
            options['extra-args']) if options['extra-args'] else input('message: ')
        splitted = []
        while status_text:
            splitted.append(status_text[:140])
            status_text = status_text[140:]

        if options['invert-split']:
            splitted.reverse()
        for status in splitted:
            fanfou.statuses.update(status=status)


class HelpAction(Action):
    def __call__(self, fanfou, options):
        print(__doc__)


class ReplAction(Action):
    def __call__(self, fanfou, options):
        print_nicely(
            "\nUse the 'fanfou' object to interact with the Fanfou REST API.\n\n")
        code.interact(local={'fanfou': fanfou, 'f': fanfou})


ACTIONS = {
    'authorize': DoNothingAction,
    'follow': FollowAction,
    'friends': FriendsAction,
    'help': HelpAction,
    'leave': LeaveAction,
    'replies': RepliesAction,
    'search': SearchAction,
    'set': SetStatusAction,
    'repl': ReplAction,
}


def main(args=sys.argv[1:]):
    try:
        arg_options = parse_args(args)
    except GetoptError as e:
        print("I can't do that, {}.".format(e), file=sys.stderr)
        sys.exit(1)

    config_path = os.path.expanduser(
        arg_options.get('config-filename') or OPTIONS.get('config-filename'))
    config_options = load_config(config_path)

    options = OPTIONS.copy()
    for d in config_options, arg_options:
        for k, v in d.items():
            options[k] = v

    if options['refresh'] and options['action'] not in ('friends', 'replies'):
        print('You can only refresh the friends or replies actions.', file=sys.stderr)
        print("Use 'fanpy -h' for help.", file=sys.stderr)
        sys.exit(1)

    oauth_filename = os.path.expanduser(options['oauth-filename'])
    if options['action'] == 'authorize' or not os.path.exists(oauth_filename):
        oauth_dance('The Command-Line Tool', CONSUMER_KEY, CONSUMER_SECRET, oauth_filename)

    global ansi_formatter
    ansi_formatter = ansi.AnsiCmd(options['force-ansi'])

    oauth_token, oauth_token_secret = read_token_file(oauth_filename)
    fanfou = Fanfou(auth=OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

    try:
        Action()(fanfou, options)
    except NoSuchActionError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except FanfouError as e:
        print(str(e), file=sys.stderr)
        print("Use 'fanpy -h' for help.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
