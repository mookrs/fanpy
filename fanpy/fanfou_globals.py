"""
    List of Fanfou method names that require the use of POST.
"""

POST_ACTIONS = [

    # Status Methods
    'update',

    # Direct-messages Methods
    'new',

    # Account Methods
    'update_notify_num', 'update_profile', 'update_profile_image',

    # Blocks Methods, Friendships Methods, Favorites Methods,
    # Saved-searches Methods
    'create',

    # Statuses Methods, Blocks Methods, Direct-messages Methods,
    # Friendships Methods, Favorites Methods, Saved-searches Methods
    'destroy',

    # Friendships Methods
    'accept', 'deny',

    # Users Methods
    'cancel_recommendation',

    # Photo Methods
    'upload',

    # OAuth Methods
    'token', 'access_token',
    'request_token', 'invalidate_token',
]
