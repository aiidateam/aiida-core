from django.contrib.auth.models import User
from tastypie import fields, utils
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.validation import Validation
from tastypie.serializers import Serializer
from aiida.djsite.db.models import (
        DbAuthInfo, 
        DbAttribute,
        DbExtra,
        DbComputer, 
        DbGroup,
        DbNode,
        )
from aiida.transport import Transport, TransportFactory
from aiida.scheduler import Scheduler, SchedulerFactory

class MyDateSerializer(Serializer):
    """
    Our own serializer to format datetimes in ISO 8601 but with timezone
    offset.
    """
    def format_datetime(self, data):
        from django.utils.timezone import is_naive
        # If naive or rfc-2822, default behavior...
        if is_naive(data) or self.datetime_formatting == 'rfc-2822':
            return super(MyDateSerializer, self).format_datetime(data)
        
        return data.isoformat()


class DbComputerValidation(Validation):
    def is_valid(self, bundle, request=None):
        """
        Check the validity of provided data for a computer.
        
        :note: if you need to modify data, one should inherit from the
            CleanedDataFormValidation class.
        
        :return: an empty dictionary means no error.
            Otherwise, a dictionary with key=field with error,
            and value=list of errors, even if there is only one.
        """
        if not bundle.data:
            return {'__all__': 'No data found...'}
        
        errors = {}
        
        ## For the time being, I only check the scheduler_type and the
        ## transport_type
        ## TODO: implement complete validation
        
        # TODO: if it is too slow, cache these?
        transports_list = Transport.get_valid_transports()
        schedulers_list = Scheduler.get_valid_schedulers()
                                
        for k, v in bundle.data.iteritems():
            if k == "transport_type":
                if v not in transports_list:
                    errors[k] = "Invalid transport type"
            elif k == "scheduler_type":
                if v not in schedulers_list:
                    errors[k] = "Invalid scheduler type"
            elif k == "name":
                if not v:
                    errors[k] = "Zero-length computer name not allowed"
        
        return errors

# To discuss/implement/activate:
# - Caching, Throttling, 

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        # Hide resources that should not be exposed to the API
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'first_name': ['exact', 'iexact'],
            'last_name': ['exact', 'iexact'],
            'username': ['exact'],         
            }
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()

class DbComputerResource(ModelResource):
    
    class Meta:
        queryset = DbComputer.objects.all()
        resource_name = 'dbcomputer'
        allowed_methods = ['get', 'post', 'patch']
        filtering = {
            'id': ALL,
            'uuid': ALL,
            'name': ALL,
            'description': ALL,
            'hostname': ALL,
            'scheduler_type': ALL,
            'transport_type': ALL,
            'enabled': ALL,
            }
        ordering = ['id', 'name', 'transport_type', 'scheduler_type', 'enabled']
        always_return_data=True

        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
        validation = DbComputerValidation()
    
    def dehydrate_metadata(self, bundle):
        import json
        
        try:
            data = json.loads(bundle.data['metadata'])
        except (ValueError, TypeError):
            data = None
        return data

    def hydrate(self, bundle):
#        from tastypie.exceptions import ImmediateHttpResponse
#        from tastypie.http import HttpForbidden

        # Remove 'uuid' and 'id' data from the modify request, if present 
        # (The 'None' default field is meant to avoid Exceptions if the field
        # is not provided)
        bundle.data.pop('uuid', None)        
        bundle.data.pop('id', None)
#        raise ImmediateHttpResponse(
#            HttpForbidden("Modification not allowed.")
#            )                                   
        return bundle

    def hydrate_metadata(self, bundle):
        import json
        
        bundle.data['metadata'] = json.dumps(bundle.data['metadata'])
        
        return bundle

    def hydrate_transport_params(self, bundle):
        import json
        
        bundle.data['transport_params'] = json.dumps(bundle.data['transport_params'])
        
        return bundle

    def dehydrate_transport_params(self, bundle):
        import json
        
        try:
            data = json.loads(bundle.data['transport_params'])
        except (ValueError, TypeError):
            data = None
        return data

    def build_schema(self):
        """
        Improve the information provided in the schema
        """
        # Get the default schema
        new_schema = super(DbComputerResource, self).build_schema()
        
        ###########################################
        # VALID CHOICES FOR TRANSPORT AND SCHEDULER
        tlist = Transport.get_valid_transports()
        slist = Scheduler.get_valid_schedulers()

        tdict = {}
        sdict = {}
        for tname in tlist:
            t = TransportFactory(tname)
            tdict[tname] = {'doc': t.get_short_doc()}
        for sname in slist:
            s = SchedulerFactory(sname)
            sdict[sname] = {'doc': s.get_short_doc()}
        # Add the required fields
        new_schema['fields']['scheduler_type']['valid_choices'] = sdict
        new_schema['fields']['transport_type']['valid_choices'] = tdict

        ############################################
        # Fix the 'type' values, where appropriate
        new_schema['fields']['metadata']['type'] = "dictionary"
        new_schema['fields']['transport_params']['type'] = "dictionary"
        
        #hardcoded by VB for testing purposes
        new_schema['fields']['description']['display_name'] = "Description" #not necessary if the name is just capitalized
        new_schema['fields']['description']['filtering'] = {"type": "text"} #not necessary, take from the type
        new_schema['fields']['enabled']['display_name'] = "Enabled"
        new_schema['fields']['enabled']['filtering'] = {"type": "boolean"}
        new_schema['fields']['hostname']['display_name'] = "Hostname"
        new_schema['fields']['hostname']['filtering'] = {"type": "text"}
        new_schema['fields']['id']['display_name'] = "ID"
        new_schema['fields']['id']['filtering'] = {"type": "numeric"}
        new_schema['fields']['name']['display_name'] = "Name"
        new_schema['fields']['name']['filtering'] = {"type": "text"}
        new_schema['fields']['scheduler_type']['display_name'] = "Scheduler"
        new_schema['fields']['scheduler_type']['filtering'] = {"type": "list"}
        new_schema['fields']['transport_type']['display_name'] = "Transport"
        new_schema['fields']['transport_type']['filtering'] = {"type": "list"}
        new_schema['fields']['uuid']['display_name'] = "Unique ID"
        new_schema['fields']['uuid']['filtering'] = {"type": "text"}
        
        return new_schema


class DbAuthInfoResource(ModelResource):
    # TODO: IMPORTANT! 
    # Implement here a authorization allowing each user to see only his own
    # entries, as shown for instance here:
    # http://django-tastypie.readthedocs.org/en/latest/authorization.html
    aiidauser = fields.ToOneField(UserResource, 'aiidauser', full=True) 
    dbcomputer = fields.ToOneField(DbComputerResource, 'dbcomputer')
    
    class Meta:
        queryset = DbAuthInfo.objects.all()
        resource_name = 'dbauthinfo'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'dbcomputer': ALL_WITH_RELATIONS,
            'aiidauser': ALL_WITH_RELATIONS,
            }
        
        authentication = SessionAuthentication()
        # As discussed above: improve this with authorization allowing each
        # user to see only his own DbAuthInfo data
        authorization = DjangoAuthorization()

    def dehydrate_auth_params(self, bundle):
        import json
        
        try:
            data = json.loads(bundle.data['auth_params'])
        except (ValueError, TypeError):
            data = None
        return data


class DbGroupResource(ModelResource):
    user = fields.ToOneField(UserResource, 'user') 
    dbnodes = fields.ToManyField('aiida.djsite.db.api.DbAttributeResource', 'dbnodes', related_name='dbgroups')    
    
    class Meta:
        queryset = DbGroup.objects.all()
        resource_name = 'dbgroup'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'user': ALL,
            'dbnodes': ALL_WITH_RELATIONS,
            'time': ALL,
            'description': ALL,
            'name': ALL,
            'uuid': ['exact'],
            }


def never(bundle):
    return False

class DbNodeResource(ModelResource):
    user = fields.ToOneField(UserResource, 'user')
    # Full = False: only put 
    outputs = fields.ToManyField('self', 'outputs', related_name='inputs', full=False, use_in='detail')   
    inputs = fields.ToManyField('self', 'inputs', related_name='outputs', full=False, use_in='detail')

    dbattributes = fields.ToManyField('aiida.djsite.db.api.DbAttributeResource', 'dbattributes', related_name='dbnode', full=False, use_in='detail')
    dbextras = fields.ToManyField('aiida.djsite.db.api.DbExtraResource', 'dbextras', related_name='dbnode', full=False, use_in='detail')

    ## Transitive-closure links
    ## Hidden for the time being, they could be too many
    children = fields.ToManyField('self', 'children', related_name='parents', full=False, use_in=never)
    parents = fields.ToManyField('self', 'parents', related_name='children', full=False, use_in=never)
    
    computer = fields.ToOneField(DbComputerResource, 'computer', null=True)
    
    class Meta:
        queryset = DbNode.objects.all()
        resource_name = 'dbnode'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'uuid': ALL,
            'type': ALL,   
            'ctime': ALL,
            'mtime': ALL,
            'label': ALL,
            'description': ALL,
            'computer': ALL_WITH_RELATIONS,
            'dbattributes': ALL_WITH_RELATIONS,
            'dbextras': ALL_WITH_RELATIONS,
            'user': ALL_WITH_RELATIONS,
            'outputs': ALL_WITH_RELATIONS,
            'inputs': ALL_WITH_RELATIONS,
            'parents': ALL_WITH_RELATIONS,
            'children': ALL_WITH_RELATIONS,  
            'attributes': ALL_WITH_RELATIONS,    
            }

        ordering = ['id', 'label', 'type', 'computer', 'ctime']
        authentication = SessionAuthentication()
        # As discussed above: improve this with authorization allowing each
        # user to see only his own DbAuthInfo data
        authorization = DjangoAuthorization()
        serializer = MyDateSerializer()

class DbAttributeResource(ModelResource):
    dbnode = fields.ToOneField(DbNodeResource, 'dbnode', related_name='dbattributes')    
    class Meta:
        queryset = DbAttribute.objects.all()
        resource_name = 'dbattribute'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'dbnode': ALL_WITH_RELATIONS,
            'datatype': ['exact'],
            'key': ALL,
            'bval': ALL,   
            'dval': ALL,
            'fval': ALL,
            'ival': ALL,
            'tval': ALL,
            'time': ALL,
            }
        serializer = MyDateSerializer()
        

class DbExtraResource(ModelResource):
    dbnode = fields.ToOneField(DbNodeResource, 'dbnode', related_name='dbextras')    
    class Meta:
        queryset = DbExtra.objects.all()
        resource_name = 'dbextra'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'dbnode': ALL_WITH_RELATIONS,
            'datatype': ['exact'],
            'key': ALL,
            'bval': ALL,   
            'dval': ALL,
            'fval': ALL,
            'ival': ALL,
            'tval': ALL,
            'time': ALL,
            }
        
        
# class MetadataResource(ModelResource):
#     dbnode = fields.ToOneField(DbNodeResource, 'dbnode', related_name='metadata')    
#     class Meta:
#         queryset = DbAttribute.objects.all()
#         resource_name = 'metadata'
#         allowed_methods = ['get']
#         filtering = {
#             'id': ['exact'],
#             'dbnode': ALL_WITH_RELATIONS,
#             'datatype': ['exact'],
#             'key': ALL,
#             'time': ALL,
#             }
#         
#     def build_filters(self,filters=None):
#         from django.db.models import Q
#         
#         if filters is None:
#             filters = {}
#             
#         orm_filters = super(MetadataResource, self).build_filters(filters)
#         orm_filters['custom'] = ~Q(key__startswith="_") 
#         
#         return orm_filters
#     
#     def apply_filters(self, request, applicable_filters):
#         custom = applicable_filters.pop('custom',None)
#         
#         pre_filtered = super(MetadataResource, self).apply_filters(request, applicable_filters)
#         if custom is not None:
#             return pre_filtered.filter(custom)
#         else:
#             return pre_filtered
#         
#     def dehydrate(self, bundle):
#         # Remove all the fields with name matching the pattern '?val'
#         # (bval, ival, tval, dval, fval, ...)
# 
#         # I have to make a list out of it otherwise I get a
#         # "dictionary changed during iteration" error
#         for k in list(bundle.data.keys()):
#             if len(k) == 4 and k.endswith('val'):
#                 del bundle.data[k]
#         
#         ## I leave the datatype, can be useful
#         #datatype = bundle.data.pop('datatype')
#         
#         bundle.data['value'] = bundle.obj.getvalue()
#         
#         return bundle

