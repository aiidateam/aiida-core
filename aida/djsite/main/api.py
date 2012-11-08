from tastypie import fields
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

from aida.djsite.main.models import Struc, Calc, CalcAttrNum, CalcAttrNumVal

class StrucResource(ModelResource):
    inpcalc = fields.ToManyField('aida.djsite.main.api.CalcResource', 'inpcalc',related_name='inpstruc')
    outcalc = fields.ToManyField('aida.djsite.main.api.CalcResource', 'outcalc', related_name='outstruc')
    class Meta:
        queryset = Struc.objects.all()
        filtering = {
            'inpcalc': ALL_WITH_RELATIONS,
            'outcalc': ALL_WITH_RELATIONS,
            }
        allowed_method = ['get']
        include_resource_uri = True    

class CalcResource(ModelResource):
     # Set full=True if you want to put the value instead of the URI
    calcattrnumval=fields.ToManyField('aida.djsite.main.api.CalcAttrNumValResource', 'calcattrnumval')

    class Meta:
        queryset = Calc.objects.all()
        filtering = {
            'calcattrnumval': ALL_WITH_RELATIONS,
            }
        allowed_method = ['get']
        #excludes = ['id']
        include_resource_uri = True
        #authentication = BasicAuthentication()
        #authorization = DjangoAuthorization()

class CalcAttrNumValResource(ModelResource):
    item = fields.ToOneField('aida.djsite.main.api.CalcResource', 'item')
    attr = fields.ToOneField('aida.djsite.main.api.CalcAttrNumResource', 'attr')

    class Meta:
        queryset = CalcAttrNumVal.objects.all()
        filtering = {
            'item': ALL_WITH_RELATIONS,
            'attr': ALL_WITH_RELATIONS,
            'val': ALL,
            }
        allowed_method = ['get']
        include_resource_uri = True

class CalcAttrNumResource(ModelResource):
    calcattrnumval_set = fields.ToManyField('aida.djsite.main.api.CalcAttrNumValResource', 'calcattrnumval_set', related_name='attr')

    class Meta:
        queryset = CalcAttrNum.objects.all()
        filtering = {
            'calcattrnumval_set': ALL_WITH_RELATIONS,
            'title': ALL,
            }
        allowed_method = ['get']
        include_resource_uri = True
