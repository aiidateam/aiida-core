##### `profile.py`

# def _dump_data(self):
#     # logger.report(f'entity_counter: {self.entity_counter}')

#     self.entity_counter = CollectionDumper.create_entity_counter()

#     for data_class in DEFAULT_DATA_TO_DUMP:
#         # ? Could also do try/except, as key only in `entity_counter` when instances of type in group
#         if self.entity_counter.get(data_class, 0) > 0:
#             # logger.report(data_class)
#             data_nodes = get_nodes_from_db(aiida_node_type=data_class, flat=True)
#             for data_node in data_nodes:
#                 # logger.report(f'{type(data_node)}: {data_node}')
#                 # logger.report(f'{isinstance(data_node, orm.StructureData)}')

#                 datadumper = DataDumper(overwrite=True)

#                 # Must pass them implicitly here, rather than, e.g. `data_node=data_node`
#                 # Otherwise `singledispatch` raises: `IndexError: tuple index out of range`
#                 datadumper.dump(data_node, self.parent_path)

#             # print(data_nodes)

    # def resolve_dump_entities(self):
    #     if WorkflowNode in self.entities_to_dump:
    #         self.dump_workflows()
    #     if StructureData in self.entities_to_dump:
    #         self.dump_structures()
    #     if CalculationNode in self.entities_to_dump:
    #         self.dump_calculations()
    #     if Code in self.entities_to_dump or Computer in self.entities_to_dump:
    #         self.dump_code_computers()
    #     if User in self.entities_to_dump:
    #         self.dump_user_info()
    #     # ? Possibly do this by default?
    #     if Profile in self.entities_to_dump:
    #         self.dump_profile_info()

    # def dump_structures(self, format: str = 'cif'):
    #     structure_datas = get_nodes_from_db(aiida_node_type=StructureData, with_group=self.current_group)

    #     for structure_data_ in structure_datas:
    #         # QB returns list...
    #         structure_data = structure_data_[0]

    #         structures_path = Path(self.parent_path / self.group_sub_path / 'structures')

    #         structures_path.mkdir(exist_ok=True, parents=True)

    #         structure_name = f'{structure_data.get_formula()}-{structure_data.pk}.{format}'

    #         if self.full:
    #             structure_data.export(path=structures_path / structure_name, fileformat=format, overwrite=True)
    #         else:
    #             try:
    #                 structure_data.export(path=structures_path / structure_name, fileformat=format, overwrite=False)
    #                 self.entities_to_dump
    #             # This is basically a FileExistsError
    #             except OSError:
    #                 continue

    def dump(self):
        if self.full:
            logger.report('Full set to True. Will overwrite previous directories.')
            validate_make_dump_path(
                overwrite=True, path_to_validate=self.parent_path, logger=logger, safeguard_file=PROFILE_DUMP_JSON_FILE
            )

        # logger.report('Dumping groups...')

        self._dump_groups()

        logger.report('Dumping data nodes.')
        self._dump_data()

    def _dump_groups(self):
        # # ? These here relate to sorting by groups
        # self.group_sub_path = Path()

        profile_groups = QueryBuilder().append(Group).all(flat=True)
        # core_groups = [group for group in profile_groups if group.type_string == 'core']
        # import_groups = [group for group in profile_groups if group.type_string == 'core.import']
        non_import_groups = [group for group in profile_groups if not group.type_string.startswith('core.import')]
        # pseudo_groups = [group for group in profile_groups if group.type_string.startswith('pseudo')]

        # self.profile_groups = profile_groups

        for group in non_import_groups:
            group_subdir = Path(*group.type_string.split('.'))
            group_dumper = GroupDumper(parent_path=self.parent_path)
            # logger.report(
            #     f'self.parent_path / "groups" / group_subdir / group.label: {self.parent_path / group_subdir / group.label}'
            # )
            group_dumper.dump(
                group=group,
                output_path=self.parent_path / 'groups' / group_subdir / group.label,
            )

            # structures_path.mkdir(exist_ok=True, parents=True)

        # if self.organize_by_groups:
        #     LOGGER.report('Dumping sorted by groups.')
        #     for group in self.profile_groups:
        #         LOGGER.report(f'Dumping group: {group}')
        #         self.current_group = group
        #         self.group_sub_path = self.parent_path / 'groups' / Path(self.current_group.label)
        #         self.resolve_dump_entities()
        # else:
        #     self.resolve_dump_entities()

        # self.update_info_file()

        # print('hello from dump')
        # print('self.entity_counter_dictionary', self.entity_counter_dictionary)
            def dump_workflows(self, only_parents: bool = True):
        # ? Dump only top-level workchains, as that includes sub-workchains already

        if self.organize_by_groups:
            workflows = get_nodes_from_db(aiida_node_type=WorkflowNode, with_group=self.current_group)
        else:
            workflows = get_nodes_from_db(aiida_node_type=WorkflowNode)

        for iworkflow_, workflow_ in enumerate(workflows):
            workflow = workflow_[0]

            if only_parents and workflow.caller is not None:
                continue

            workflow_dumper = ProcessDumper(**self.process_dumper_kwargs, overwrite=self.full)

            workflow_dump_path = (
                self.parent_path
                / self.group_sub_path
                / ProcessDumper._generate_default_dump_path(process_node=workflow)
            )

            if not self.dry_run:
                with contextlib.suppress(FileExistsError):
                    workflow_dumper.dump(process_node=workflow, output_path=workflow_dump_path)

            self.entity_counter_dictionary[WorkflowNode.__name__] += 1

            # To make development quicker
            if iworkflow_ > 1:
                break


##### `collection.py`

    # def dump(self):
    #     orm_entities = self._retrieve_orm_entities()

    #     for orm_entity in orm_entities:
    #         if isinstance(orm_entity, orm.ProcessNode):
    #             process_dumper = ProcessDumper(**self.kwargs)
    #             # process_dumper.pretty_print()
    #             print(process_dumper)
    #         elif isinstance(orm_entity, orm.Data):
    #             data_dumper = DataDumper(**self.kwargs)
    #         break

    def dump_processes(self, group: orm.Group | str | None = None, output_path: Path | str | None = None):
        # ? Here, these could be all kinds of entities that could be grouped in AiiDA
        # if output_path is None:
        #     output_path = Path.cwd()

        self.last_dumped = timezone.now()
        self.group = group

        if group is None:
            raise Exception('Group must be set')

        self.group_name = group.label if isinstance(group, orm.Group) else group

        if output_path is None:
            try:
                output_path = self.parent_path / 'groups' / self.group_name
            except:
                raise ValueError('Error setting up `output_path`. Must be set manually.')
        else:
            # TODO: Add validation here
            output_path.mkdir(exist_ok=True, parents=True)

        self.create_entity_counter(group=group)
        pprint(self.entity_counter)

        self.hidden_aiida_path = self.parent_path / '.aiida-raw-data'

        # ? This here now really relates to each individual group
        self.output_path = output_path
        # self.group_path = Path.cwd() / 'groups'
        # self.group_path = self.output_path / 'groups' / group_name

        # logger.report(f'self.entity_counter for Group <{self.group}>: {self.entity_counter}')
        # logger.report(f'Dumping calculations and workflows of group {group_name}...')

        # TODO: This shouldn't be on a per-group basis? Possibly dump all data for the whole profile.
        # TODO: Though, now that I think about it, it might actually be desirable to only limit that to the group only.
        # logger.report(f'Dumping raw calculation data for group {group_name}...')

        if self.dump_processes:
            # if self.should_dump_calculations() or self.should_dump_workflows():
            logger.report(f'Dumping calculations for group {self.group_name}...')

            # def _obtain_workflows(): ...
            workflows = [node for node in self.group.nodes if isinstance(node, orm.WorkflowNode)]

            # Also need to obtain sub-calculations that were called by workflows of the group
            # These are not contained in the group.nodes directly
            called_calculations = []
            for workflow in workflows:
                called_calculations += [
                    node for node in workflow.called_descendants if isinstance(node, orm.CalculationNode)
                ]

            calculations = set(
                [node for node in self.group.nodes if isinstance(node, orm.CalculationNode)] + called_calculations
            )

            self._dump_calculations_hidden(calculations=calculations)
            self._dump_link_workflows(workflows=workflows)
            self._link_calculations_hidden(calculations=calculations)

    def dump_data(self):
        # data = [node for node in self.group.nodes if isinstance(node, orm.Data)]
        data = [node for node in self.group.nodes if isinstance(node, orm.StructureData)]
        # print('DATA', data)
        self._dump_data_hidden(data_nodes=data)

    @staticmethod
    def _obtain_calculations():
        raise NotImplementedError('This should be implemented in subclasses.')

    @staticmethod
    def _obtain_workflows():
        raise NotImplementedError('This should be implemented in subclasses.')


##### `rich.py`

# default_core_export_mapping = dict.fromkeys(core_data_entry_points, None)

# core_data_with_exports = [
#     # 'core.array',
#     'core.array.bands',  # ? -> Yes, though `core.bands` on CLI
#     # 'core.array.kpoints',  # ? -> Doesn't have a `verdi data` CLI endpoint
#     # 'core.array.projection',  # ? -> Doesn't have a `verdi data` CLI endpoint
#     'core.array.trajectory',  # ? -> Yes, though `core.trajectory` on CLI
#     # 'core.array.xy',  # ? -> Doesn't have a `verdi data` CLI endpoint
#     # 'core.base',  # ? -> Here it doesn't make sense
#     # 'core.bool',  # ? -> Would we even need to dump bools?
#     'core.cif',
#     # 'core.code',  # ? -> Not a `data` command. However, code export exists
#     # 'core.code.containerized',
#     # 'core.code.installed',
#     # 'core.code.portable',
#     # 'core.dict',  # ? No `export` CLI command, but should be easy as .txt
#     # 'core.enum',
#     # 'core.float',
#     # 'core.folder',  # ? No `verdi data export` endpoint, but should already be dumped anyway?
#     # 'core.int',
#     # 'core.jsonable',  # ? This implements `to_dict`, which should be easily exportable in JSON format then
#     # 'core.list',
#     # 'core.numeric',
#     # 'core.orbital',
#     # 'core.remote',
#     # 'core.remote.stash',
#     # 'core.remote.stash.folder',
#     # 'core.singlefile',  # ? Doesn't implement export, but should be simple enough to use method of class to write the
#     # file to disk
#     # 'core.str',
#     'core.structure',  # ? Yes, implements export nicely
#     'core.upf',  # ? Also implements it, but deprecated
# ]

# Default for the ones that have `verdi data core.XXX export` endpoint
# ! Is this actually preferred, rather than hardcoding. Hardcoding shouldn't be too fragile, and we don't expect to
# ! introduce new core data types...
# for core_data_with_export in core_data_with_exports:
#     default_core_export_mapping[core_data_with_export] = data_export

core_data_entry_points = [
    'core.array',
    'core.array.bands',
    'core.array.kpoints',
    'core.array.projection',
    'core.array.trajectory',
    'core.array.xy',
    'core.base',
    'core.bool',
    'core.cif',
    'core.code',
    'core.code.containerized',
    'core.code.installed',
    'core.code.portable',
    'core.dict',
    'core.enum',
    'core.float',
    'core.folder',
    'core.int',
    'core.jsonable',
    'core.list',
    'core.numeric',
    'core.orbital',
    'core.remote',
    'core.remote.stash',
    'core.remote.stash.folder',
    'core.singlefile',
    'core.str',
    'core.structure',
    'core.upf',
]

@classmethod
def set_core_defaults(cls):
    # This uses the entry points and the default mapping
    # By default, the default exporters and formats are being used
    # If the user provides an empty entry, it is set to null
    # Like this, file types can be selective turned off
    # -> It would be annoying then to manually turn off all the file types. There should be some option to `invert`,
    # e.g. `--rich-invert`, or in the config-file/rich-options

    # from importlib.metadata import entry_points

    # options_dict = {}

    # # Load all entry points under the specified group
    # entry_point_group = entry_points(group='aiida.data')

    # # print('USING DEFAULTS')

    # for entry_point in entry_point_group:
    #     entry_point_name = entry_point.name
    #     # print(entry_point_name)

    #     try:
    #         value_dict =
    #             default_core_export_mapping[entry_point_name],
    #             default_core_format_mapping[entry_point_name],
    #         )
    #         options_dict[entry_point_name] = value_tuple
    #     except:
    #         pass

    return default_core_export_mapping

##### process.py
    # def __str__(self):
    #     from tabulate import tabulate
    #     # Prepare data for the table
    #     table_data = []
    #     headers = ["Attribute", "Value"]

    #     # Iterate over the class attributes
    #     for attr_name in dir(self):
    #         # Exclude private attributes and dunder methods
    #         if not (attr_name.startswith('_') or attr_name.endswith('_')):
    #             attr_value = getattr(self, attr_name)
    #             table_data.append([attr_name, str(attr_value)])

    #     # Create a table using tabulate
    #     return tabulate(table_data, headers, tablefmt="grid")

                    # Here, one wouldn't even need the DataDumper, one could just run it like this:
                # if exporter.__name__ == 'data_export':
                #     exporter(
                #         node=node,
                #         output_fname=rich_output_file,
                #         fileformat=fileformat,
                #         other_args=None,
                #         overwrite=True,
                #     )