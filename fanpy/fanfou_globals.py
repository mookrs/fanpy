"""
    List of Fanfou method names that require the use of POST.
    Don't use '/' before method name.
"""

POST_ACTIONS = [

    # Status Methods
    'statuses/destroy', 'statuses/update', 'statuses/',

    # Photo Methods
    'photos/upload',

    # Direct Message Methods
    'direct_messages/destroy', 'direct_messages/new',

    # Account Methods
    'account/find_friends', 'account/update_notify_num', 'account/update_profile', 'account/update_profile_image',

    # Block Methods, Friendship Methods, Favorite Methods, Search Methods
    'blocks/create', 'blocks/destroy',
    'friendships/accept', 'friendships/create', 'friendships/', 'friendships/deny', 'friendships/destroy',
    'favorites/create', 'favourites/', 'favorites/destroy',
    'saved_searches/create',

    # OAuth Methods
    'token', 'access_token',
    'request_token', 'invalidate_token',
]
