###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for getting multi line input from the commandline."""

import re

import click


def edit_multiline_template(template_name: str, comment_marker: str = '#=', extension: str = '', **kwargs: dict) -> str:
    """Open a template file for editing in a text editor.

    :param template: name of the template to use from the ``aiida.cmdline.templates`` directory.
    :param comment_marker: the set of symbols that mark a comment line that should be stripped from the final value
    :param extension: the file extension to give to the rendered template file.
    :param kwargs: keywords that will be passed to the template rendering engine.
    :return: the final string value entered in the editor with all comment lines stripped or an empty string if the
        ``click.edit`` returned ``None``.
    """
    from aiida.cmdline.utils.templates import env

    template = env.get_template(template_name)
    rendered = template.render(**kwargs)
    content = click.edit(rendered, extension=extension)

    if content is not None:
        # Remove all comments, which are all lines that start with the comment marker
        return re.sub(f'(^{re.escape(comment_marker)}.*$\n)+', '', content, flags=re.M).strip()

    return ''


def edit_comment(old_cmt=''):
    """Call up an editor to edit comments to nodes in the database"""
    from aiida.cmdline.utils.templates import env

    template = env.get_template('new_cmt.txt.tpl')
    content = template.render(old_comment=old_cmt)
    mlinput = click.edit(content, extension='.txt')
    if mlinput:
        regex = r'^(?!#=)(.*)$'
        cmt = '\n'.join(re.findall(regex, mlinput, flags=re.M))
        cmt = cmt.strip('\n')
    else:
        cmt = ''
    return cmt
