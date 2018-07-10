# -*- coding: utf-8 -*-
"""
utilities for getting multi line input from the commandline
"""
import click


def edit_pre_post(pre=None, post=None, summary=None):
    """
    use click to call up an editor to write or edit pre / post
    execution scripts for both codes and computers
    """
    from aiida.cmdline.utils.templates import env
    template = env.get_template('prepost.bash.tpl')
    summary = summary or {}
    summary = {k: v for k, v in summary.iteritems() if v}
    content = template.render(default_pre=pre or '', default_post=post or '', summary=summary)
    mlinput = click.edit(content, extension='.bash')
    if mlinput:
        import re
        stripped_input = re.sub(r'(^#.*$\n)+', '#', mlinput, flags=re.M).strip('#')
        pre, post = [text.strip() for text in stripped_input.split('#')]
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
