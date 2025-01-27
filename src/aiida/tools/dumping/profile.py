###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

# TODO: Use `batch_iter` from aiida.tools.archive.common

from __future__ import annotations

import logging
import itertools as it
from rich.pretty import pprint
from pathlib import Path

from collections import Counter
from aiida import orm
from aiida.manage.configuration.profile import Profile
from aiida.tools.dumping.base import BaseDumper
from aiida.tools.dumping.group import GroupDumper
from aiida.tools.dumping.process import ProcessDumper

logger = logging.getLogger(__name__)


class ProfileDumper:
    def __init__(
        self,
        profile: str | Profile,
        base_dumper: BaseDumper | None = None,
        process_dumper: ProcessDumper | None = None,
        organize_by_groups: bool = True,
        deduplicate: bool = True,
        groups: list[str | orm.Group] | None = None,
        dump_processes: bool = True,
    ):
        self.organize_by_groups = organize_by_groups
        self.deduplicate = deduplicate
        self.profile = profile
        self.dump_processes = dump_processes
        self.groups = groups

        if base_dumper is None:
            base_dumper = BaseDumper()
        self.base_dumper: BaseDumper = base_dumper

        if process_dumper is None:
            process_dumper = ProcessDumper()
        self.process_dumper: ProcessDumper = process_dumper

        # self.log_dict: dict[dict[str, Path]] = {}
        self.log_dict= {'calculations': {}, 'workflows': {}}

    def dump(self):
        if not self.groups:
            self._dump_processes_not_in_any_group()
            self.groups = orm.QueryBuilder().append(orm.Group).all(flat=True)

        self._dump_processes_per_group()

    def _dump_processes_not_in_any_group(self):
        # === Dump the data that is not associated with any group ===
        if self.organize_by_groups:
            output_path = self.base_dumper.dump_parent_path / 'no-group'
        else:
            output_path = self.base_dumper.dump_parent_path

        no_group_dumper = GroupDumper(
            base_dumper=self.base_dumper,
            process_dumper=self.process_dumper,
            group=None,
            deduplicate=self.deduplicate,
            output_path=output_path,
            global_log_dict=self.log_dict,
        )

        if self.dump_processes and no_group_dumper._should_dump_processes():
            logger.report(f'Dumping processes not in any group for profile `{self.profile.name}`...')

            no_group_dumper._dump_processes()

            self.log_dict.update(no_group_dumper.log_dict)

    def _dump_processes_per_group(self):
        # === Dump data per-group if Groups exist in profile or are selected ===

        for group in self.groups:
            if self.organize_by_groups:
                output_path = self.base_dumper.dump_parent_path / group.label
            else:
                output_path = self.base_dumper.dump_parent_path

            group_dumper = GroupDumper(
                base_dumper=self.base_dumper,
                process_dumper=self.process_dumper,
                group=group,
                deduplicate=self.deduplicate,
                output_path=output_path,
                global_log_dict=self.log_dict,
            )

            if self.dump_processes and group_dumper._should_dump_processes():
                logger.report(f'Dumping processes in group {group.label} for profile `{self.profile.name}`...')

                group_dumper._dump_processes()
                for entity in ['calculations', 'workflows']:
                    self.log_dict[entity].update(group_dumper.log_dict[entity])

                pprint(group_dumper.log_dict)
                pprint(self.log_dict)

