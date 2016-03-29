# -*- coding: utf-8 -*-

from aiida.orm.data.parameter import ParameterData
from aiida.workflows2.process import Process
from aiida.workflows2.workflow import Workflow

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class LegacyJobCalculation(Process):
    @classmethod
    def build(cls, calc_class):

        def _init(spec):
            for k, v in calc_class._use_methods.iteritems():
                spec.add_input(v['linkname'], help=v.get('docstring', None))
            spec.add_output()

        return type(calc_class.__name__, (LegacyJobCalculation,),
                    {'_init': staticmethod(_init),
                     '_calc_class': calc_class})

    def __init__(self):
        super(LegacyJobCalculation, self).__init__()

    def _run(self, **kwargs):
        self._calc = self._calc_class()
        for k, v in kwargs.iteritems():
            self._calc['use_{}'.format(k)](v)
        # TODO: Here we need to actually call the scheduler to send the job
        self._calc._presubmit(folder)

        # TODO: Emit outputs

    def _create_db_record(self):
        return self._calc


class LegacyParser(Process):
    @classmethod
    def build(cls, parser_class, output_file_name):
        class FakeCalculation(object):
            _OUTPUT_FILE_NAME = output_file_name

            def __init__(self):
                self._retrieved_node = None

            @staticmethod
            def get_state(self):
                from aiida.common.datastructures import calc_states
                return calc_states.PARSING

            def set_retrieved_node(self, node):
                self._retrieved_node = node

            def _get_linkname_retrieved(self):
                pass

            def get_retrieved_node(self):
                return self._retrieved_node

        def _init(spec):
            spec.add_output(parser_class.get_linkname_outparams(),
                            type=ParameterData)

        return type(parser_class.__name__, (LegacyParser,),
                    {'_parser_class': parser_class,
                     '_init': staticmethod(_init),
                     '_fake_calc_class': FakeCalculation})

    def __init__(self):
        super(LegacyParser, self).__init__()
        self._fake_calc = self._fake_calc_class()
        self._parser = self._parser_class(self._fake_calc)

    def _run(self, **kwargs):
        # TODO: Set up the dummy calculation as needed for parsing
        self._fake_calc.set_retrieved_node(kwargs['retrieved'])

        parsed_ok, outs_list = self._parser.parse_from_calc()
        if parsed_ok:
            for name, value in outs_list:
                self.out(name, value)


class LegacyCalculationWorkflow(Workflow):
    @classmethod
    def build_from_calc(cls, calc_class):
        calc = calc_class()

        def _init(spec):
            spec.add_process(LegacyJobCalculation.build(calc_class), "calc")
            spec.add_process(LegacyParser.build(calc.get_parserclass()), "prase")
            spec.expose_inputs("calc")
            spec.expose_outputs("parse")

            # Link up the calculation and parser
            spec.link("calc:{}".format(calc._get_linkname_retrieved()),
                      "parse:{}".format(PARSER_INPUT_NAME))

        return type(calc_class.__name__, (LegacyCalculationWorkflow,),
                    {'_init': staticmethod(_init)})
