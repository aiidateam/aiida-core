"""Create, configure, manage users"""


def get_or_new_user(**kwargs):
    """find an existing user or instantiate a new one (unstored)"""
    from aiida.orm import User
    candidates = User.search_for_users(**kwargs)
    if candidates:
        user = candidates[0]
        created = False
    else:
        user = User(**kwargs)
        created = True
    return user, created
