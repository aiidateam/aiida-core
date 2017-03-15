# -*- coding: utf-8 -*-



def normalize_email(email):
    """
    Normalize the address by lowercasing the domain part of the email
    address.

    Taken from Django.
    """
    email = email or ''
    try:
        email_name, domain_part = email.strip().rsplit('@', 1)
    except ValueError:
        pass
    else:
        email = '@'.join([email_name, domain_part.lower()])
    return email