from django.contrib.auth.models import User
from tastypie import fields
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
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'patch', 'delete']
        filtering = {
            'id': ALL,
            'uuid': ALL,
            'name': ALL,
            'description': ALL,
            'hostname': ALL,
            'scheduler_type': ALL,
            'transport_type': ALL,
            'transport_params': ALL,
            'enabled': ALL,
            }
        ordering = ['id', 'name', 'transport_type', 'scheduler_type', 'enabled']
        always_return_data=True

        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()
        validation = DbComputerValidation()
    
    def delete_detail(self, request, **kwargs):
        """
        Delete a computer. Allow it only if there are no DbNodes using the
        given computer.
        """
        from tastypie.http import HttpConflict
        from django.db.models.deletion import ProtectedError
        
        try:
            return super(DbComputerResource, self).delete_detail(request, **kwargs)
        except ProtectedError as e:
            return HttpConflict("The DbComputer cannot be deleted, since it "
                                "is used by at least one DbNode.")
    
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
        from aiida.common.utils import create_display_name
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
        new_schema['fields']['metadata']['default'] = {}
        new_schema['fields']['transport_params']['type'] = "dictionary"
        new_schema['fields']['transport_params']['default'] = {}

        # Autogenerate display_name; specific names will be fixed below
        for field in new_schema['fields']:
            new_schema['fields'][field]['display_name'] = create_display_name(
                field)

        # Some keys require a specific name that cannot be autogenerated
        new_schema['fields']['id']['display_name'] = "ID"
        new_schema['fields']['resource_uri']['display_name'] = "Resource URI"
        new_schema['fields']['transport_params']['display_name'] = "Transport Parameters"
        new_schema['fields']['uuid']['display_name'] = "Unique ID"
        
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
            'enabled': ALL,
            'metadata': ALL,
            'auth_params': ALL,
            }
        
        authentication = SessionAuthentication()
        # As discussed above: improve this with authorization allowing each
        # user to see only his own DbAuthInfo data
        authorization = DjangoAuthorization()

    def obj_create(self, bundle, **kwargs):
        """
        This will be used when also new entries can be saved, to automatically
        enforce the association of the new DbAuthInfo to the logged-in user
        """
        return super(DbAuthInfoResource, self).obj_create(
            bundle, aiidauser=bundle.request.user)

    def apply_authorization_limits(self, request, object_list):
        """
        Show only DbAuthInfo of the logged-in user
        """
        return object_list.filter(aiidauser=request.user)

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

def only_dbattributes_levelzero(bundle):
    # Returns only level-zero attributes.
    # Put here to check if it works, but must be probably moved somewhere else
    from django.db.models import Q

    return DbAttribute.objects.filter(~Q(key__contains=DbAttribute._sep),
                                      dbnode=bundle.obj)

class DbNodeResource(ModelResource):
    
    user = fields.ToOneField(UserResource, 'user')
    # Full = False: only put 
    outputs = fields.ToManyField('self', 'outputs', related_name='inputs',
                                 full=False, use_in='detail')   
    inputs = fields.ToManyField('self', 'inputs', related_name='outputs',
                                full=False, use_in='detail')

    # Provided for querying, but not visible
    dbattributes = fields.ToManyField('aiida.djsite.db.api.DbAttributeResource',
        'dbattributes', related_name='dbnode', full=False, use_in=never)
    dbextras = fields.ToManyField('aiida.djsite.db.api.DbExtraResource',
        'dbextras', related_name='dbnode', full=False, use_in=never)
   
    #attributes = fields.ToManyField('aiida.djsite.db.api.AttributeResource',
    #                                only_dbattributes_levelzero,
    #                                null=True, related_name='dbnode',
    #                                full=False, use_in='detail')

    ## Transitive-closure links
    ## Hidden for the time being, they could be too many
    children = fields.ToManyField('self', 'children', related_name='parents',
                                  full=False, use_in=never)
    parents = fields.ToManyField('self', 'parents', related_name='children',
                                 full=False, use_in=never)
    
    dbcomputer = fields.ToOneField(DbComputerResource, 'dbcomputer', null=True)
    
    class Meta:
        queryset = DbNode.objects.all()
        resource_name = 'dbnode'
        allowed_methods = ['get']
        filtering = {
            'id': ALL, #['exact']
            'uuid': ALL,
            'type': ALL,   
            'ctime': ALL,
            'mtime': ALL,
            'label': ALL,
            'description': ALL,
            'dbcomputer': ALL_WITH_RELATIONS,
            'dbattributes': ALL_WITH_RELATIONS,
            'dbextras': ALL_WITH_RELATIONS,
            'user': ALL_WITH_RELATIONS,
            'outputs': ALL_WITH_RELATIONS,
            'inputs': ALL_WITH_RELATIONS,
            'parents': ALL_WITH_RELATIONS,
            'children': ALL_WITH_RELATIONS,
            }

        ordering = ['id', 'label', 'type', 'dbcomputer', 'ctime', 'state']
        authentication = SessionAuthentication()
        # As discussed above: improve this with authorization allowing each
        # user to see only his own DbAuthInfo data
        authorization = DjangoAuthorization()
        serializer = MyDateSerializer()

    def hydrate(self, bundle):
        """
        Prepare data before DB modification
        """
        # TODO: proper management of attributes, when storing!
        
        # Remove autogenerated fields, if present 
        bundle.data.pop('base_class', None)        
        bundle.data.pop('plugin_string', None)        
        bundle.data.pop('class_name', None)  
        bundle.data.pop('state', None)      
        return bundle

    def full_dehydrate(self, bundle, for_list=False):
        new_bundle = super(DbNodeResource, self).full_dehydrate(bundle, for_list)
        
        if for_list: # list view
            try:
                del bundle.data['attributes']
            except KeyError:
                # No attributes
                pass
        else: # detail view
            try:
                del bundle.data['state']
                del bundle.data['scheduler_state']
            except KeyError:
                # No attributes
                pass                
        
        return new_bundle

    def dehydrate(self, bundle):
        """
        Add some specific fields before serialization
        """
        from aiida.common.exceptions import DbContentError
        from aiida.common.pluginloader import get_class_typestring
        
        #############################################################
        # Get the attributes dictionary
        #############################################################
        bundle.data['attributes'] = bundle.obj.attributes
        
        #############################################################
        # Parse the type string
        #############################################################
        # Default values in case of problems        
        bundle.data['base_class'] = None
        bundle.data['plugin_string'] = None
        bundle.data['class_name'] = None
        node_type = bundle.data['type']
        try:
            (bundle.data['base_class'],
             bundle.data['plugin_string'],
             bundle.data['class_name']) = (
                get_class_typestring(node_type))
        except DbContentError:
            # Leave None as value
            pass
        if bundle.data['base_class'] == 'calculation':
            bundle.data['state'] = bundle.data['attributes']['state']
            bundle.data['scheduler_state'] = bundle.data['attributes']['scheduler_state']
        
        return bundle

    def build_schema(self):
        """
        Improve the information provided in the schema
        """
        from aiida.common.utils import create_display_name
        # Get the default schema
        new_schema = super(DbNodeResource, self).build_schema()
        
        # User-defined fields
        new_schema['fields']['base_class'] = {
            "blank": True,
            "default": "",
            "help_text": "The base class of the node (can either be node, "
                         "calculation, code or data).",
            "nullable": False,
            "readonly": True,
            "type": "string",
            "unique": False,
            }
        new_schema['fields']['plugin_string'] = {
            "blank": True,
            "default": "",
            "help_text": "The string that can be passed to the proper factory "
                         "(e.g. DataFactory, or CalculationFactory) to load "
                         "dynamically the proper class.",
            "nullable": False,
            "readonly": True,
            "type": "string",
            "unique": False,
            }
        new_schema['fields']['class_name'] = {
            "blank": True,
            "default": "",
            "help_text": "The name of the Python class associated to this node.",
            "nullable": False,
            "readonly": True,
            "type": "string",
            "unique": False,
            }
        new_schema['fields']['attributes'] = {
            "blank": False,
            "default": {},
            "help_text": "The attributes associated to this node.",
            "nullable": False,
            "readonly": False,
            "type": "dictionary",
            "unique": False,
            }
        # Extras are instead provided only with an endpoint
                
        # Autogenerate display_name; specific names will be fixed below
        for field in new_schema['fields']:
            new_schema['fields'][field]['display_name'] = create_display_name(
                field)

        # Some keys require a specific name that cannot be autogenerated
        new_schema['fields']['id']['display_name'] = "ID"
        new_schema['fields']['resource_uri']['display_name'] = "Resource URI"
        new_schema['fields']['uuid']['display_name'] = "Unique ID"
        new_schema['fields']['ctime']['display_name'] = "Creation Time"
        new_schema['fields']['mtime']['display_name'] = "Modification Time"
        
        return new_schema

    def prepend_urls(self):
        """
        Add some endpoints
        """
        from django.conf.urls.defaults import url
        from tastypie.utils import trailing_slash
        
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/extras%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_extras'), name="api_get_dbnode_extras"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/attributes%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_attributes'), name="api_get_dbnode_attributes"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/inputs%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_inputs'), name="api_get_dbnode_inputs"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/outputs%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_outputs'), name="api_get_dbnode_outputs"),
        ]

    def get_outputs(self, request, **kwargs):
        """
        Return a list of inputs.
        """
        from django.core.exceptions import (
            ObjectDoesNotExist,
            MultipleObjectsReturned,
            )
        from tastypie.http import HttpGone, HttpMultipleChoices
        from aiida.djsite.db.models import DbLink
        from aiida.common.exceptions import DbContentError
        from aiida.common.pluginloader import get_class_typestring
        
        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']},
                                       request=request)
            obj = self.cached_obj_get(bundle=bundle,
                                      **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        values = DbLink.objects.filter(input=obj.pk).values(
            'output__pk', 'label', 'output__type', 'output__label').order_by('pk')

#        new_bundle = self.build_bundle(data={'pk': 197},
#                                   request=request)           
        data = {"outputs": 
            [{'id': i['output__pk'],
              'link_name': i['label'], 
              'resource_uri': self.get_uri_for_pk(i['output__pk']),
              'type': i['output__type'],
              'label': i['output__label']
              }
             for i in values]}
        
        for i in data['outputs']:
            try:
                (i['base_class'],
                 i['plugin_string'],
                 i['class_name']) = (
                    get_class_typestring(i['type']))
                del i['type']
            except DbContentError:
                # Skip this input (leaving only the 'type' string) and continue
                continue
        
        return self.create_response(request, data)

    def get_inputs(self, request, **kwargs):
        """
        Return a list of inputs.
        """
        from django.core.exceptions import (
            ObjectDoesNotExist,
            MultipleObjectsReturned,
            )
        from tastypie.http import HttpGone, HttpMultipleChoices
        from aiida.djsite.db.models import DbLink
        from aiida.common.exceptions import DbContentError
        from aiida.common.pluginloader import get_class_typestring
        
        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']},
                                       request=request)
            obj = self.cached_obj_get(bundle=bundle,
                                      **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        values = DbLink.objects.filter(output=obj.pk).values(
            'input__pk', 'label', 'input__type', 'input__label').order_by('pk')

#        new_bundle = self.build_bundle(data={'pk': 197},
#                                   request=request)           
        data = {"inputs": 
            [{'id': i['input__pk'],
              'link_name': i['label'], 
              'resource_uri': self.get_uri_for_pk(i['input__pk']),
              'type': i['input__type'],
              'label': i['input__label']
              }
             for i in values]}
        
        for i in data['inputs']:
            try:
                (i['base_class'],
                 i['plugin_string'],
                 i['class_name']) = (
                    get_class_typestring(i['type']))
                del i['type']
            except DbContentError:
                # Skip this input (leaving only the 'type' string) and continue
                continue
        
        return self.create_response(request, data)

    @classmethod
    def get_uri_for_pk(cls, pk):
        from django.core.urlresolvers import reverse
        
        uri = reverse("api_dispatch_detail", kwargs={
            'api_name': cls._meta.api_name,
            'resource_name': cls._meta.resource_name, 
            'pk': pk})
        return uri

    def get_extras(self, request, **kwargs):
        """
        Return a dictionary with the extras.
        """
        from django.core.exceptions import (
            ObjectDoesNotExist,
            MultipleObjectsReturned,
            )
        from tastypie.http import HttpGone, HttpMultipleChoices
        
        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']},
                                       request=request)
            obj = self.cached_obj_get(bundle=bundle,
                                      **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        data = obj.extras
        return self.create_response(request, data)
    
    def get_attributes(self, request, **kwargs):
        """
        Return a dictionary with the attributes.
        """
        from django.core.exceptions import (
            ObjectDoesNotExist,
            MultipleObjectsReturned,
            )
        from tastypie.http import HttpGone, HttpMultipleChoices
        
        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']},
                                       request=request)
            obj = self.cached_obj_get(bundle=bundle,
                                      **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        data = obj.attributes
        return self.create_response(request, data)


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
        

class AttributeResource(ModelResource):
    dbnode = fields.ToOneField(DbNodeResource, 'dbnode', related_name='attributes')    
    class Meta:
        queryset = DbAttribute.objects.all()
        resource_name = 'attribute'
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
         
    def dehydrate(self, bundle):
        # Remove all the fields with name matching the pattern '?val'
        # (bval, ival, tval, dval, fval, ...)
 
        # I have to make a list out of it otherwise I get a
        # "dictionary changed during iteration" error
        for k in list(bundle.data.keys()):
            if len(k) == 4 and k.endswith('val'):
                del bundle.data[k]
         
        ## I leave the datatype, can be useful
        #datatype = bundle.data.pop('datatype')
         
        bundle.data['value'] = bundle.obj.getvalue()
         
        return bundle



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
        serializer = MyDateSerializer()
        
        
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

