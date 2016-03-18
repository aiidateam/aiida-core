# -*- coding: utf-8 -*-


from aiida.workflows2.process import Process
from aiida.workflows2.workflow import Workflow

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class LegacyJobCalculation(Process):
    @classmethod
    def build(cls, calc_type):

        def _init(spec):
            for k, v in calc_type._use_methods.iteritems():
                spec.add_input(v['linkname'], help=v.get('docstring', None))

        return type(calc_type.__name__, (LegacyJobCalculation,),
                    {'_init': staticmethod(_init),
                     '_calc_type': calc_type)

    def __init__(self):
        super(LegacyJobCalculation, self).__init__()

    def _run(self, **kwargs):
        self._calc = self._calc_type()
        for k, v in kwargs.iteritems():
            self._calc['use_{}'.format(k)](v)
        # TODO: Here we need to actually call the scheduler to send the job
        self._calc._presubmit(folder)

    def _create_db_record(self):
        return self._calc


class LegacyParser(Process):
    @classmethod
    def build(cls, parser_type, output_file_name):
        class FakeCalculation(object):
            _OUTPUT_FILE_NAME = ""

            def __init__(self, output_file_name):
                self._OUTPUT_FILE_NAME = output_file_name

            @staticmethod
            def get_state(self):
                from aiida.common.datastructures import calc_states
                return calc_states.PARSING

            def _get_linkname_retrieved(self):
                pass

        def init():
            pass

        return type(parser_type.__name__, (LegacyParser,),
                    {'_parser_type': parser_type,
                     '_init': staticmethod(init),
                     '_fake_calc': FakeCalculation(output_file_name)})

    def __init__(self):
        super(LegacyParser, self).__init__()
        self._parser = self._parser_type(self._fake_calc)

    def _run(self, **kwargs):
        # TODO: Set up the dummy calculation as needed for parsing
        parsed_ok, outs_list = self._parser.parse_from_calc()
        if parsed_ok:
            return {out[0]: out[1] for out in outs_list}


class LegacyCalculationWorkflow(Workflow):
    @classmethod
    def build_from_calc(cls, calc):
        # TODO: Use the calculation instance to construct an appropriate workflow
        pass
