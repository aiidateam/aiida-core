from django.contrib.auth.models import User
from tastypie import fields, utils
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from aiida.djsite.db.models import (
        DbAuthInfo, 
        DbAttribute,
        DbComputer, 
        DbGroup,
        DbNode,
        )

# To discuss/implement/activate:
# - Authentication + authorization
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


class DbComputerResource(ModelResource):
    
    class Meta:
        queryset = DbComputer.objects.all()
        resource_name = 'dbcomputer'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'uuid': ALL,
            'name': ALL,
            'description': ALL,
            'hostname': ALL,
            'scheduler_type': ALL,
            'transport_type': ALL,
            'workdir': ALL,
            }
        ordering = ['id', 'name', 'transport_type', 'scheduler_type', 'enabled'] 
    
    def dehydrate_metadata(self, bundle):
        import json
        
        try:
            data = json.loads(bundle.data['metadata'])
        except (ValueError, TypeError):
            data = None
        return data

class DbAuthInfoResource(ModelResource):
    aiidauser = fields.ToOneField(UserResource, 'aiidauser', full=True) 
    computer = fields.ToOneField(DbComputerResource, 'computer')
    
    class Meta:
        queryset = DbAuthInfo.objects.all()
        resource_name = 'dbauthinfo'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'computer': ALL_WITH_RELATIONS,
            'aiidauser': ALL_WITH_RELATIONS,
            }

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

    dbattributes = fields.ToManyField('aiida.djsite.db.api.DbAttributeResource', 'attributes', related_name='dbnode', full=False, use_in='detail')
    attributes = fields.ToManyField('aiida.djsite.db.api.AttributeResource', 'attributes', related_name='dbnode', full=False, use_in='detail')

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
            'ctype': ALL,
            'mtype': ALL,
            'label': ALL,
            'description': ALL,
            'computer': ALL_WITH_RELATIONS,
            'dbattributes': ALL_WITH_RELATIONS,
            'user': ALL_WITH_RELATIONS,
            'outputs': ALL_WITH_RELATIONS,
            'inputs': ALL_WITH_RELATIONS,
            'parents': ALL_WITH_RELATIONS,
            'children': ALL_WITH_RELATIONS,  
            'attributes': ALL_WITH_RELATIONS,    
            }

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
            'time': ALL,
#            'key': ALL,
#            'value': ALL,
            }
        
    def build_filters(self,filters=None):
        if filters is None:
            filters = {}
            
        orm_filters = super(AttributeResource, self).build_filters(filters)
        orm_filters['key__startswith'] = "_"
        
        return orm_filters
    
    def dehydrate_key(self, bundle):
        return bundle.data['key'][1:]
    
    def dehydrate(self, bundle):
        # Remove all the fields with name matching the pattern '?val'
        # (bval, ival, tval, dval, fval, ...)
        for k in bundle.data.keys():
            if len(k) == 4 and k.endswith('val'):
                del bundle.data[k]
        
        ## I leave the datatype, can be useful
        #datatype = bundle.data.pop('datatype')
        
        bundle.data['value'] = bundle.obj.getvalue()
        
        return bundle
        
class MetadataResource(ModelResource):
    dbnode = fields.ToOneField(DbNodeResource, 'dbnode', related_name='metadata')    
    class Meta:
        queryset = DbAttribute.objects.all()
        resource_name = 'metadata'
        allowed_methods = ['get']
        filtering = {
            'id': ['exact'],
            'dbnode': ALL_WITH_RELATIONS,
            'datatype': ['exact'],
            'key': ALL,
            'time': ALL,
            }
        
    def build_filters(self,filters=None):
        from django.db.models import Q
        
        if filters is None:
            filters = {}
            
        orm_filters = super(MetadataResource, self).build_filters(filters)
        orm_filters['custom'] = ~Q(key__startswith="_") 
        
        return orm_filters
    
    def apply_filters(self, request, applicable_filters):
        custom = applicable_filters.pop('custom',None)
        
        pre_filtered = super(MetadataResource, self).apply_filters(request, applicable_filters)
        if custom is not None:
            return pre_filtered.filter(custom)
        else:
            return pre_filtered
        
    def dehydrate(self, bundle):
        # Remove all the fields with name matching the pattern '?val'
        # (bval, ival, tval, dval, fval, ...)
        for k in bundle.data.keys():
            if len(k) == 4 and k.endswith('val'):
                del bundle.data[k]
        
        ## I leave the datatype, can be useful
        #datatype = bundle.data.pop('datatype')
        
        bundle.data['value'] = bundle.obj.getvalue()
        
        return bundle

