# -*- coding: utf-8 -*-

import aiida.workflows2.persistance.file_store as file_store

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


def create_process_record(process, inputs):
    return file_store.FileActiveProcess(
        process.__class__.__name__,
        {label: inp.uuid for label, inp in inputs.iteritems()})

#
# def create_workflow_record(process, inputs):
#     return file_store.FileActiveWorkflow(
#         process.__class__,
#         {label: inp.uuid for label, inp in inputs.iteritems()})


def load_all_process_records():
    return file_store.FileActiveProcess.load_all()
