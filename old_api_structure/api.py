from tastypie import fields
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

from aiida.djsite.main.models import Structure, Calculation, CalcAttrNum, CalcAttrNumVal

class StructureResource(ModelResource):
    incalculations = fields.ToManyField('aiida.djsite.main.api.CalculationResource', 'incalculations',related_name='instructures')
    outcalculations = fields.ToManyField('aiida.djsite.main.api.CalculationResource', 'outcalculations', related_name='outstructures')

    class Meta:
        queryset = Structure.objects.all()
        filtering = {
            'incalculations': ALL_WITH_RELATIONS,
            'outcalculations': ALL_WITH_RELATIONS,
            }
        allowed_methods = ['get']
        include_resource_uri = True    

    def apply_filters(self, request, applicable_filters):
        """
        Overridden to get only distinct results
        """
        return self.get_object_list(request).filter(**applicable_filters).distinct()

class CalculationResource(ModelResource):
     # Set full=True if you want to put the value instead of the URI
    calcattrnumval=fields.ToManyField('aiida.djsite.main.api.CalcAttrNumValResource', 'calcattrnumval',related_name='calcattrnumval')

    class Meta:
        queryset = Calculation.objects.all()
        filtering = {
            'calcattrnumval': ALL_WITH_RELATIONS,
            }
        allowed_methods = ['get']
        #excludes = ['id']
        include_resource_uri = True
        #authentication = BasicAuthentication()
        #authorization = DjangoAuthorization()

class CalcAttrNumValResource(ModelResource):
    calculation = fields.ToOneField('aiida.djsite.main.api.CalculationResource',
                                    'calculation')
    attribute = fields.ToOneField('aiida.djsite.main.api.CalcAttrNumResource', 
                                  'attribute')

    class Meta:
        queryset = CalcAttrNumVal.objects.all()
        filtering = {
            'calculation': ALL_WITH_RELATIONS,
            'attribute': ALL_WITH_RELATIONS,
            'value': ALL,
            }
        allowed_methods = ['get']
        include_resource_uri = True

class CalcAttrNumResource(ModelResource):
    calcattrnumval_set = fields.ToManyField('aiida.djsite.main.api.CalcAttrNumValResource', 'calcattrnumval_set', related_name='attribute')

    class Meta:
        queryset = CalcAttrNum.objects.all()
        filtering = {
            'calcattrnumval_set': ALL_WITH_RELATIONS,
            'name': ALL,
            }
        allowed_methods = ['get']
        include_resource_uri = True
