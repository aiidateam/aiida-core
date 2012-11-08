from tastypie import fields
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

from aida.djsite.main.models import Struc, Calc, CalcAttrNum, CalcAttrNumVal

class StrucResource(ModelResource):
    inpcalc = fields.ToManyField('CalcResource', 'inpcalc')
    outcalc = fields.ToManyField('CalcResource', 'outcalc')
    class Meta:
        queryset = Calc.objects.all()
        filtering = {
            'inpcalc': ALL_WITH_RELATIONS,
            'outcalc': ALL_WITH_RELATIONS,
            }
        allowed_method = ['get']
        include_resource_uri = True    

class CalcResource(ModelResource):
     # Set full=True if you want to put the value instead of the URI
    attrnum=fields.ToManyField('CalcAttrNumResource', 'attrnum')

    class Meta:
        queryset = Calc.objects.all()
        filtering = {
            'attrnum': ALL_WITH_RELATIONS,
            }
        allowed_method = ['get']
        #excludes = ['id']
        include_resource_uri = True
        #authentication = BasicAuthentication()
        #authorization = DjangoAuthorization()

class CalcAttrNumValResource(ModelResource):
    item = fields.ToOneField('CalcResource', 'item')
    attr = fields.ToOneField('CalcAttrNumResource', 'attr')

    class Meta:
        queryset = Calc.objects.all()
        filtering = {
            'item': ALL_WITH_RELATIONS,
            'attr': ALL_WITH_RELATIONS,
            }
        allowed_method = ['get']
        include_resource_uri = True


class CalcAttrNumResource(ModelResource):
    calcattrnumval_set = fields.ToManyField('CalcAttrNumValResource', 'calcattrnumval_set', related_name='attr')

    class Meta:
        queryset = Calc.objects.all()
        filtering = {
            'attr_set': ALL_WITH_RELATIONS,
            }
        allowed_method = ['get']
        include_resource_uri = True
