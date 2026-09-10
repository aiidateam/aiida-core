## Motivation

### Performance

The schema generation is expensive and is only needed when orm classes leave the process boundary.
There are two use cases that fulfill this constraint which are CLI usage (`Computer` and `Code` creation, maybe extended by `Profile`) and the REST API.
The schema generation should only happen for these use cases.

### User API

Workflow developers are supposed to only extend the data nodes, so any logic we expose there should be simple.
Data nodes do not require a CLI model, only `Computer`, `Code`, and `Profile` do, so  we can put any logic deciding if a field is part of the CLI model into a different field.
For the REST API model its a bit more tricky, while the logic for each data node is **mostly** the same (Add the attributes and only reference the files in the repository so we apply some file transfer logic when sending or receiving files), there is the valid use case to validate the construction of the orm class froma POST request.
So the workflow developer still ideally puts the validation on the attribute type into the field and not in the `__init__` constructor
For example fo StructureData this would mean that the `__init__` constructor still converts ase to the cell, but then any validation on top (e.g. `_get_valid_cell`) would need to be defined in the field definition.
So overall this is the motivation to have attribute field (in PoC `AttributeField`) as part of user API keeping its option minimal to reduce burden on workflow developer and a more generic field (in PoC called `ColumnField`) as part of core API which defines behavior of the field when converted to a pydantic field in the building of the CLI and REST API model.

## Implementation details

I want that the initialization through the `__init__` constructor and the model deserialization are consistent.
While in the model deserialzation its applied by pydantic automatically, in the python object we don't have any mechanisum like this.
I don't want that the user explicitely needs to call the validator of the field that is to error prone.
Therefore I introduced `self.base.columns.<column_field_name>` following the usage of the attributes.
When one sets a column field in the python object the validator is triggered automatically.
The same behavior has been implemented for the attributes.

I introduced `_attribute_fields` in `DataNode` so it is clear that this is part of the user API. while the `_column_fields` is only defined in the core API.
Effectively, these fields are just merged later one when building the model, the distinction is purely motivated due to API separation concerns.

I kept the information how the `ColumnField` is converted to a `RestApiField` or `CliField` in the member variables of `ColumnField`.
When buildling for example the `RestApiModel`, we first convert `AttributeField`s and `ColumnField`s to `RestApiField` to then convert these to `pydantic.Field`.
It is just exists for code reusabilty but in principle all information lies in `ColumnField` and `AttributeField` to convert to a `pydantic.Field`. 

## Breaking changes

I did not want to include back the `orm_to_cli`, `cli_to_orm` and vice versa for the REST API in the fields because it introduces complexity that is not needed.
Why do we need to convert them before serializing?
The fields type is already restricted through the database serializability and introducing such options is another potential point of failure in the round trip (I think the existing code is buggy for commands that have a whitespace in an argument e.g. `mpirun -np 4 myapp --extra-args "-O3 -unbuffered"`).
This breaks the exsting CLI format for Computer (`mpirun_command` is stored as string in the json and as list of strings in the orm class) but overall the downstream effects seem minimal to me.
