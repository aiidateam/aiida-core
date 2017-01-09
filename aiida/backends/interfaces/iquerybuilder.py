from abc import abstractmethod, ABCMeta


class IQueryBuilder():
    __metaclass__ = ABCMeta
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass
    @abstractmethod
    def prepare_with_dbpath(self):
        """
        A method to use the DbPath, if this is supported, or throw an
        exception if not.
        The overrider must fill add the DbPath-ORM as an attribute to self::

            from aiida.backends.implementation.model import DbPath
            self.path = DbPath

        """
        pass
    @abstractmethod
    def get_session(self):
        pass

    @abstractmethod
    def modify_expansions(self, alias, expansions):
        """
        Modify names of projections if ** was specified.
        This is important for the schema having attributes in a different table.
        """
        pass

    @abstractmethod
    def get_filter_expr_from_attributes(
            cls, operator, value, attr_key,
            column=None, column_name=None, alias=None):
        pass
    @abstractmethod
    def get_projectable_attribute(
            self, alias, column_name, attrpath,
            cast=None, **kwargs):
        pass
    @abstractmethod
    def get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param key: the key that this entry would be returned with
        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        pass

    @abstractmethod
    def get_ormclass(self,  cls, ormclasstype):
        pass


    @abstractmethod
    def yield_per(self, batch_size):
        """
        :param count: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        pass

    @abstractmethod
    def count(self):
        pass

    @abstractmethod
    def first(self):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """

        pass
    @abstractmethod
    def iterall(self, batch_size=100):
        pass

    @abstractmethod
    def iterdict(self, batch_size=100):
        pass


