# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy.types import Integer, String, Boolean, DateTime, Text, Float
from aiida.backends.sqlalchemy.models.base import Base
from aiida.utils import timezone



class DbSetting(Base):
    __tablename__ = "db_dbsetting"

    id = Column(Integer, primary_key=True)

    key = Column(String(255), index = True, nullable = False)
    datatype = Column(String(10), index = True, nullable = False)
    
    tval = Column(String(255), default = '', nullable = True)
    fval = Column(Float, default = None, nullable = True)
    ival = Column(Integer, default = None, nullable = True)
    bval = Column(Boolean, default=None, nullable=True)
    dval = Column(DateTime, default=None, nullable = True)

    # I also add a description field for the variables
    description = Column(String(255), default = '', nullable = True)
    time = Column(DateTime(timezone=True), default=timezone.now)

    _sep = "."

    def __str__(self):
        return "'{}'={}".format(self.key, self.getvalue())
    

    # There are no subspecifiers. If instead you want to group attributes
    # (e.g. by node, as it is done in the DbAttributeBaseClass), specify here
    # the field name
    _subspecifier_field_name = None

    @property
    def subspecifiers_dict(self):
        """
        Return a dict to narrow down the query to only those matching also the
        subspecifier.
        """
        if self._subspecifier_field_name is None:
            return {}
        else:
            return {self._subspecifier_field_name:
                        getattr(self, self._subspecifier_field_name)}

    @property
    def subspecifier_pk(self):
        """
        Return the subspecifier PK in the database (or None, if no
        subspecifier should be used)
        """
        if self._subspecifier_field_name is None:
            return None
        else:
            return getattr(self, self._subspecifier_field_name).pk

    @classmethod
    def validate_key(cls, key):
        """
        Validate the key string to check if it is valid (e.g., if it does not
        contain the separator symbol.).

        :return: None if the key is valid
        :raise ValidationError: if the key is not valid
        """
        from aiida.common.exceptions import ValidationError

        if not isinstance(key, basestring):
            raise ValidationError("The key must be a string.")
        if not key:
            raise ValidationError("The key cannot be an empty string.")
        if cls._sep in key:
            raise ValidationError("The separator symbol '{}' cannot be present "
                                  "in the key of a {}.".format(
                cls._sep, cls.__name__))

    @classmethod
    def set_value(cls, key, value, with_transaction=True,
                  subspecifier_value=None, other_attribs={},
                  stop_if_existing=False):
        """
        Set a new value in the DB, possibly associated to the given subspecifier.

        :note: This method also stored directly in the DB.

        :param key: a string with the key to create (must be a level-0
          attribute, that is it cannot contain the separator cls._sep).
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param with_transaction: True if you want this function to be managed
          with transactions. Set to False if you already have a manual
          management of transactions in the block where you are calling this
          function (useful for speed improvements to avoid recursive
          transactions)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).
        :param stop_if_existing: if True, it will stop with an
           UniquenessError exception if the new entry would violate an
           uniqueness constraint in the DB (same key, or same key+node,
           depending on the specific subclass). Otherwise, it will
           first delete the old value, if existent. The use with True is
           useful if you want to use a given attribute as a "locking" value,
           e.g. to avoid to perform an action twice on the same node.
           Note that, if you are using transactions, you may get the error
           only when the transaction is committed.
        """
        from aiida.backends.sqlalchemy import session

        cls.validate_key(key)

        try:
            if with_transaction:
                sid = transaction.savepoint()

            # create_value returns a list of nodes to store
            to_store = cls.create_value(key, value,
                                        subspecifier_value=subspecifier_value,
                                        other_attribs=other_attribs)

            if to_store:
                if not stop_if_existing:
                    # Delete the olf values if stop_if_existing is False,
                    # otherwise don't delete them and hope they don't
                    # exist. If they exist, I'll get an UniquenessError

                    ## NOTE! Be careful in case the extra/attribute to
                    ## store is not a simple attribute but a list or dict:
                    ## like this, it should be ok because if we are
                    ## overwriting an entry it will stop anyway to avoid
                    ## to overwrite the main entry, but otherwise
                    ## there is the risk that trailing pieces remain
                    ## so in general it is good to recursively clean
                    ## all sub-items.
                    cls.del_value(key,
                                  subspecifier_value=subspecifier_value)
                cls.objects.bulk_create(to_store)

            if with_transaction:
                transaction.savepoint_commit(sid)
        except BaseException as e:  # All exceptions including CTRL+C, ...
            from django.db.utils import IntegrityError
            from aiida.common.exceptions import UniquenessError

            if with_transaction:
                transaction.savepoint_rollback(sid)
            if isinstance(e, IntegrityError) and stop_if_existing:
                raise UniquenessError("Impossible to create the required "
                                      "entry "
                                      "in table '{}', "
                                      "another entry already exists and the creation would "
                                      "violate an uniqueness constraint.\nFurther details: "
                                      "{}".format(
                    cls.__name__, e.message))
            raise

    @classmethod
    def create_value(cls, key, value, subspecifier_value=None,
                     other_attribs={}):
        """
        Create a new list of attributes, without storing them, associated
        with the current key/value pair (and to the given subspecifier,
        e.g. the DbNode for DbAttributes and DbExtras).

        :note: No hits are done on the DB, in particular no check is done
          on the existence of the given nodes.

        :param key: a string with the key to create (can contain the
          separator cls._sep if this is a sub-attribute: indeed, this
          function calls itself recursively)
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).

        :return: always a list of class instances; it is the user
          responsibility to store such entries (typically with a Django
          bulk_create() call).
        """
        import json
        import datetime
        from aiida.utils.timezone import is_naive, make_aware, get_current_timezone

        if cls._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            new_entry = cls(key=key, **other_attribs)
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(cls.__name__,
                                                                cls._subspecifier_field_name))
            further_params = other_attribs.copy()
            further_params.update({cls._subspecifier_field_name:
                                       subspecifier_value})
            new_entry = cls(key=key, **further_params)

        list_to_return = [new_entry]

        if value is None:
            new_entry.datatype = 'none'
            new_entry.bval = None
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, bool):
            new_entry.datatype = 'bool'
            new_entry.bval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, (int, long)):
            new_entry.datatype = 'int'
            new_entry.ival = value
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, float):
            new_entry.datatype = 'float'
            new_entry.fval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.bval = None
            new_entry.dval = None

        elif isinstance(value, basestring):
            new_entry.datatype = 'txt'
            new_entry.tval = value
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, datetime.datetime):

            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value, get_current_timezone())
            else:
                value_to_set = value

            new_entry.datatype = 'date'
            # TODO: time-aware and time-naive datetime objects, see
            # https://docs.djangoproject.com/en/dev/topics/i18n/timezones/#naive-and-aware-datetime-objects
            new_entry.dval = value_to_set
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        elif isinstance(value, (list, tuple)):

            new_entry.datatype = 'list'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for i, subv in enumerate(value):
                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(cls.create_value(
                    key=("{}{}{:d}".format(key, cls._sep, i)),
                    value=subv,
                    subspecifier_value=subspecifier_value))

        elif isinstance(value, dict):

            new_entry.datatype = 'dict'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for subk, subv in value.iteritems():
                cls.validate_key(subk)

                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(cls.create_value(
                    key="{}{}{}".format(key, cls._sep, subk),
                    value=subv,
                    subspecifier_value=subspecifier_value))
        else:
            try:
                jsondata = json.dumps(value)
            except TypeError:
                raise ValueError("Unable to store the value: it must be "
                                 "either a basic datatype, or json-serializable")

            new_entry.datatype = 'json'
            new_entry.tval = jsondata
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        return list_to_return

    @classmethod
    def get_query_dict(cls, value):
        """
        Return a dictionary that can be used in a django filter to query
        for a specific value. This takes care of checking the type of the
        input parameter 'value' and to convert it to the right query.

        :param value: The value that should be queried. Note: can only be
           base datatype, not a list or dict. For those, query directly for
           one of the sub-elements.

        :todo: see if we want to give the possibility to query for the existence
           of a (possibly empty) dictionary or list, of for their length.

        :note: this will of course not find a data if this was stored in the
           DB as a serialized JSON.

        :return: a dictionary to be used in the django .filter() method.
            For instance, if 'value' is a string, it will return the dictionary
            ``{'datatype': 'txt', 'tval': value}``.

        :raise: ValueError if value is not of a base datatype (string, integer,
            float, bool, None, or date)
        """
        import datetime
        from aiida.utils.timezone import (
            is_naive, make_aware, get_current_timezone)

        if value is None:
            return {'datatype': 'none'}
        elif isinstance(value, bool):
            return {'datatype': 'bool', 'bval': value}
        elif isinstance(value, (int, long)):
            return {'datatype': 'int', 'ival': value}
        elif isinstance(value, float):
            return {'datatype': 'float', 'fval': value}
        elif isinstance(value, basestring):
            return {'datatype': 'txt', 'tval': value}
        elif isinstance(value, datetime.datetime):
            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value, get_current_timezone())
            else:
                value_to_set = value
            return {'datatype': 'date', 'dval': value_to_set}
        elif isinstance(value, list):
            raise ValueError("Lists are not supported for getting the "
                             "query_dict")
        elif isinstance(value, dict):
            raise ValueError("Dicts are not supported for getting the "
                             "query_dict")
        else:
            raise ValueError("Unsupported type for getting the "
                             "query_dict, it is {}".format(str(type(value))))

    def getvalue(self):
        """
        This can be called on a given row and will get the corresponding value,
        casting it correctly.
        """
        from aiida.common.deserialization import deserialize_attributes, DeserializationException
        try:
            if self.datatype == 'list' or self.datatype == 'dict':
                prefix = "{}{}".format(self.key, self._sep)
                prefix_len = len(prefix)
                dballsubvalues = self.__class__.objects.filter(
                    key__startswith=prefix,
                    **self.subspecifiers_dict).values_list('key',
                                                           'datatype', 'tval', 'fval',
                                                           'ival', 'bval', 'dval')
                # Strip the FULL prefix and replace it with the simple
                # "attr" prefix
                data = {"attr.{}".format(_[0][prefix_len:]): {
                    "datatype": _[1],
                    "tval": _[2],
                    "fval": _[3],
                    "ival": _[4],
                    "bval": _[5],
                    "dval": _[6],
                } for _ in dballsubvalues
                        }
                # for _ in dballsubvalues}
                # Append also the item itself
                data["attr"] = {
                    # Replace the key (which may contain the separator) with the
                    # simple "attr" key. In any case I do not need to return it!
                    "key": "attr",
                    "datatype": self.datatype,
                    "tval": self.tval,
                    "fval": self.fval,
                    "ival": self.ival,
                    "bval": self.bval,
                    "dval": self.dval}
                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self.__class__,
                                              original_pk=self.subspecifier_pk)['attr']
            else:
                data = {"attr": {
                    # Replace the key (which may contain the separator) with the
                    # simple "attr" key. In any case I do not need to return it!
                    "key": "attr",
                    "datatype": self.datatype,
                    "tval": self.tval,
                    "fval": self.fval,
                    "ival": self.ival,
                    "bval": self.bval,
                    "dval": self.dval}}

                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self.__class__,
                                              original_pk=self.subspecifier_pk)['attr']
        except DeserializationException as e:
            exc = DbContentError(e.message)
            exc.original_exception = e
            raise exc

    @classmethod
    def del_value(cls, key, only_children=False, subspecifier_value=None):
        """
        Delete a value associated with the given key (if existing).

        :note: No exceptions are raised if no entry is found.

        :param key: the key to delete. Can contain the separator cls._sep if
          you want to delete a subkey.
        :param only_children: if True, delete only children and not the
          entry itself.
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        """
        from django.db.models import Q

        if cls._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            subspecifiers_dict = {}
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(cls.__name__,
                                                                cls._subspecifier_field_name))
            subspecifiers_dict = {cls._subspecifier_field_name:
                                      subspecifier_value}

        query = Q(key__startswith="{parentkey}{sep}".format(
            parentkey=key, sep=cls._sep),
            **subspecifiers_dict)

        if not only_children:
            query.add(Q(key=key, **subspecifiers_dict), Q.OR)

        cls.objects.filter(query).delete()
