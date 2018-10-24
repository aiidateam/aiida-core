# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
utilities for getting multi line input from the commandline
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click
from aiida.common.exceptions import InputValidationError


def ensure_scripts(pre, post, summary):
    """
    A function to check if the prepend and append scripts were specified, and
    if needed ask to edit them.

    :param pre: prepend-text
    :param post: append-text
    :param summary: summary for click template
    :return:
    """
    if not pre or not post:
        return edit_pre_post(pre, post, summary)

    return pre, post


def edit_pre_post(pre=None, post=None, summary=None):
    """
    use click to call up an editor to write or edit pre / post
    execution scripts for both codes and computers
    """
    from aiida.cmdline.utils.templates import env
    template = env.get_template('prepost.bash.tpl')
    summary = summary or {}
    summary = {k: v for k, v in summary.items() if v}

    # Define a separator that will be splitting pre- and post- execution
    # parts of the submission script
    separator = "#====================================================#\n" \
                "#=               Post execution script              =#\n" \
                "#=  I am acting as a separator, do not modify me!!! =#\n" \
                "#====================================================#\n"

    content = template.render(default_pre=pre or '', separator=separator, default_post=post or '', summary=summary)
    mlinput = click.edit(content, extension='.bash')
    if mlinput:
        import re

        # Splitting the text in pre- and post- halfs
        try:
            pre, post = mlinput.split(separator)
        except ValueError as err:
            if str(err) == "need more than 1 value to unpack":
                raise InputValidationError("Looks like you modified the "
                                           "separator that should NOT be modified. Please be "
                                           "careful!")
            elif str(err) == "too many values to unpack":
                raise InputValidationError("Looks like you have more than one "
                                           "separator, while only one is needed "
                                           "(and allowed). Please be careful!")
            else:
                raise err

        # Removing all the comments starting from '#=' in both pre- and post-
        # parts
        pre = re.sub(r'(^#=.*$\n)+', '', pre, flags=re.M).strip()
        post = re.sub(r'(^#=.*$\n)+', '', post, flags=re.M).strip()
    else:
        pre, post = ('', '')
    return pre, post


def edit_comment(old_cmt=''):
    """
    call up an editor to edit comments to nodes in the database
    """
    from aiida.cmdline.utils.templates import env
    template = env.get_template('new_cmt.txt.tpl')
    content = template.render(old_comment=old_cmt)
    mlinput = click.edit(content, extension='.txt')
    if mlinput:
        import re
        regex = r'^(?!#=)(.*)$'
        cmt = '\n'.join(re.findall(regex, mlinput, flags=re.M))
        cmt = cmt.strip('\n')
    else:
        cmt = ''
    return cmt
