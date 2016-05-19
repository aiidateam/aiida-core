# -*- coding: utf-8 -*-

import re
from plum.wait_ons import Checkpoint
from aiida.workflows2.process import Process


__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "The AiiDA team"


class FragmentedWorkfunction(Process):
    class Context(object):
        _content = {}

        def __init__(self, value=None):
            if value is not None:
                for k, v in value.iteritems():
                    self._content[k] = v

        def _get_dict(self):
            return self._content

        def __getattr__(self, name):
            try:
                return self._content[name]
            except KeyError:
                raise AttributeError("Context does not have a variable {}"
                                     .format(name))

        def __setattr__(self, name, value):
            self._content[name] = value

        def __dir__(self):
            return sorted(self._content.keys())

        def __iter__(self):
            for k in self._content:
                yield k

    @staticmethod
    def _is_valid_keyword(k):
        import keyword
        return re.match("[_A-Za-z][_a-zA-Z0-9]*$", k) and not keyword.iskeyword(k)

    @staticmethod
    def _get_indent_level(s):
        g = re.match("^(\s*)([^\s])", s)
        if g is None:
            return None  # empty line
        else:
            return len(g.groups()[0])

    @staticmethod
    def _strip_block(block):
        retlist = []
        for linenum, content in block[1:]:
            if FragmentedWorkfunction._is_valid_keyword(content):
                retlist.append(content)
            else:
                raise SyntaxError("Invalid keyword at line {}: '{}'".format(linenum, content))
        return retlist

    START = '@start'
    END = '@end'

    definition = ""

    _ctx = Context()

    def __init__(self):
        super(FragmentedWorkfunction, self).__init__()
        self._last_step = None
        self._last_context = None

    def _run(self, **kwargs):
        return self._do_step()

    def _do_step(self, checkpoint=None):
        self._last_step, self._last_context =\
            self._run_from_graph(self._last_step, self._last_context)
        if self._last_step != self.END:
            return Checkpoint(self._do_step.__name__)

    def save_instance_state(self, bundle):
        for key, val in self._last_context:
            bundle[key] = val

    ## Internal messages ################################
    def on_finalise(self):
        self._last_context = None
        self._last_step = None
    #####################################################

    @property
    def ctx(self):
        return self._ctx

    def _get_graph(self):
        wfdef = self._parse_def()
        graph = self._create_graph(wfdef)
        return graph

    def _run_from_graph(self, current_step=None, last_ctx=None):
        graph = self._get_graph()

        if last_ctx is not None:
            if current_step is None:
                raise ValueError("A ctx was specified, but not current_step")
            for k, v in last_ctx.iteritems():
                setattr(self.ctx, k, v)
        else:
            if current_step is not None:
                raise ValueError("last_step was specified, but no last_ctx")

        if current_step is None:
            current_step = self.START

        step_data = graph[current_step]
        this_type = step_data['type']
        if this_type == self.END:
            return self.END, last_ctx
        this_step = step_data['method']

        if this_type == 'step':
            # manage retval here
            retval = self._run_step(this_step)
            return this_step, self.ctx._get_dict()

        elif this_type == 'condition':  # can put an optional exit clause, e.g. no more than # steps
            # TODO This logic should change if blocks caan be nested
            retval = self._run_step(this_step)  # NOTE: condition is not allowed to change context
            if retval == True:
                return self._run_from_graph(current_step="{}:true".format(this_step),
                                            last_ctx=last_ctx)
            elif retval == False:
                return self._run_from_graph(current_step="{}:false".format(this_step),
                                            last_ctx=last_ctx)
            else:
                raise ValueError("{} should return true or false, not {}".format(
                    this_step, retval))
        else:
            raise ValueError("Unknown step type {}".format(current_type))

    def _create_graph(self, wfdef):
        next_step = {}

        # All previous steps that have to be joined
        # can be more than one because e.g. both the last statement in the
        # if and in the else block have to 'merge' in the next step
        last_steps = [self.START]
        for step in wfdef:
            if isinstance(step, basestring):
                for last_step in last_steps:
                    next_step[last_step] = {'type': 'step', 'method': step}
                last_steps = [step]
            elif isinstance(step, dict):
                if step['block'] == 'while':
                    for last_step in last_steps:
                        next_step[last_step] = {'type': 'condition',
                                                'method': step['condition']}
                    next_step['{}:true'.format(step['condition'])] = {
                        'type': 'step', 'method': step['content'][0]}
                    last_steps = ['{}:false'.format(step['condition'])]
                    # Internal loop
                    for pre, nex in zip(step['content'][:-1], step['content'][1:]):
                        next_step[pre] = {'type': 'step', 'method': nex}
                    # Check at the end
                    next_step[step['content'][-1]] = {'type': 'condition',
                                                      'method': step['condition']}
                elif step['block'] == 'if':
                    for last_step in last_steps:
                        next_step[last_step] = {'type': 'condition',
                                                'method': step['condition']}

                    last_steps = []

                    next_step['{}:true'.format(step['condition'])] = {
                        'type': 'step', 'method': step['content_true'][0]}
                    for pre, nex in zip(step['content_true'][:-1],
                                        step['content_true'][1:]):
                        next_step[pre] = {'type': 'step', 'method': nex}
                    last_steps.append(step['content_true'][-1])

                    if 'content_false' in step:
                        next_step['{}:false'.format(step['condition'])] = {
                            'type': 'step', 'method': step['content_false'][0]}
                        for pre, nex in zip(step['content_false'][:-1],
                                            step['content_false'][1:]):
                            next_step[pre] = {'type': 'step', 'method': nex}
                        last_steps.append(step['content_false'][-1])
                    else:
                        last_steps.append('{}:false'.format(step['condition']))
                else:
                    raise ValueError("Invalid block type!")
            else:
                raise ValueError("Invalid type in step definition!")
        for last_step in last_steps:
            next_step[last_step] = {'type': '@end'}

        return next_step

    def _run_step(self, step_name):
        if not isinstance(step_name, basestring):
            raise TypeError("step name should be string, its value is instead {}".format(
                step_name))
        step_method = getattr(self, step_name, None)
        if step_method is None:
            raise SyntaxError("No step '{}' defined in the class".format(
                step_name))
        else:
            # print "** Current context:", self.ctx._get_dict()
            return step_method()

    def _parse_def(self):
        def_list = []

        # Only one indentation level allowed

        blocks = []
        current_indent = None

        for idx, l in enumerate(self.definition.splitlines(), start=1):
            # TODO: remove comments
            p = l.rstrip()
            if not p:
                continue  # Skip empty line

            # Check indentation level
            this_line_indent = FragmentedWorkfunction._get_indent_level(p)

            if this_line_indent == current_indent:
                blocks[-1].append((idx, p.strip()))
            else:
                current_indent = this_line_indent
                blocks.append([current_indent, (idx, p.strip())])

        skip_block = False
        zero_level = None
        for block_idx, block in enumerate(blocks):
            if skip_block:
                skip_block = False
                continue  # In next line, I should check if I'm back at level zero...
            level = block[0]
            lines = block[1:]

            if zero_level is None:
                zero_level = level
            if level != zero_level:
                raise SyntaxError("Only one level of indent is allowed (line {})".format(
                    linenum))

            for line_idx, (linenum, content) in enumerate(lines):
                if content.endswith(':'):
                    content = content[:-1].strip()  # Remove final ':'
                    if line_idx != len(lines) - 1:
                        raise SyntaxError(
                            "Wrong indentation level in definition at line {}, "
                            "block must be indented".format(lines[block_idx + 1][0]))
                    if block_idx == len(blocks) - 1:
                        raise SyntaxError(
                            "There should be an indented block after line {}"
                            ".".format(linenum))
                    if blocks[block_idx + 1] < level:
                        raise SyntaxError(
                            "The block after line {} should be further indented "
                            "than line {}".format(linenum, linenum))

                    skip_block = True  # Skip next block
                    if content.startswith('if '):
                        condition = content[3:].strip()
                        if not FragmentedWorkfunction._is_valid_keyword(condition):
                            raise SyntaxError(
                                "Invalid condition {} at line {}".format(condition,
                                                                         linenum))
                        def_list.append({'block': 'if', 'condition': condition,
                                         'content_true': FragmentedWorkfunction._strip_block(blocks[block_idx + 1])})
                    elif content == 'else':
                        if len(def_list) == 0:
                            raise SyntaxError(
                                "Lonely else block at line {}".format(linenum))
                        else:
                            if (not isinstance(def_list[-1], dict) or
                                        def_list[-1]['block'] != 'if'):
                                raise SyntaxError(
                                    "Lonely else block at line {}".format(linenum))
                            def_list[-1]['content_false'] = FragmentedWorkfunction._strip_block(
                                blocks[block_idx + 1])
                    elif content.startswith('while '):
                        condition = content[6:].strip()
                        if not FragmentedWorkfunction._is_valid_keyword(condition):
                            raise SyntaxError(
                                "Invalid condition {} at line {}".format(condition,
                                                                         linenum))
                        def_list.append({'block': 'while', 'condition': condition,
                                         'content': FragmentedWorkfunction._strip_block(blocks[block_idx + 1])})
                    else:
                        raise SyntaxError(
                            "Unknown block type {} at line {} ({})".format(content.split()[0],
                                                                           linenum, content))
                else:
                    if FragmentedWorkfunction._is_valid_keyword(content):
                        def_list.append(content)
                    else:
                        raise SyntaxError(
                            "Invalid keyword {} at line {}".format(content, linenum))

        return def_list
