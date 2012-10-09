from aidadb.models import *
#from django_orm.postgresql.hstore.expressions import HstoreExpression as HE


def InitData():
    cs1 = CodeStatus.objects.get_or_create(title='debug')[0]
    cs2 = CodeStatus.objects.get_or_create(title='stable')[0]
    ct1 = CodeType.objects.get_or_create(title='espresso')[0]
    ct2 = CodeType.objects.get_or_create(title='vasp')[0]
    st1 = StrucType.objects.get_or_create(title='molecule')[0]
    st2 = StrucType.objects.get_or_create(title='crystal')[0]
#    ss1 = StrucStatus.objects.get_or_create(title='icsd')
#    ss2 = StrucStatus.objects.get_or_create(title='generated')
    cas1 = CalcStatus.objects.get_or_create(title='finished')[0]
    cas2 = CalcStatus.objects.get_or_create(title='running')[0]
    cat1 = CalcType.objects.get_or_create(title='relax')[0]
    cat2 = CalcType.objects.get_or_create(title='neb')[0]
    u = AuthUser.objects.get(username='kyb5pal')
    print u
    comp = Computer.objects.get_or_create(title='hal', hostname='palhpc.bosch.com', 
                                  # ip_address='192.168.0.1', 
                                   workdir='/scratch')[0]
    
    p1 = Project.objects.get_or_create(title='Battery')[0]
    p2 = Project.objects.get_or_create(title='Piezo')[0]
    
    code1 = Code.objects.get_or_create(title='pwscf', type=ct1, status=cs1, user=u)[0]
    code2 = Code.objects.get_or_create(title='vasp', type=ct2, status=cs2, user=u)[0]

    s1 = Struc.objects.get_or_create(title='s1', formula='H2O', user=u, type=st1)[0]
    s2 = Struc.objects.get_or_create(title='s2', formula='CH4', user=u, type=st1)[0]
    s3 = Struc.objects.get_or_create(title='s3', formula='K', user=u, type=st2)[0]
    s4 = Struc.objects.get_or_create(title='s4', formula='NaCl', user=u, type=st2)[0]
    
    c1 = Calc.objects.get_or_create(title='c1', user=u, type=cat1, status=cas1, code=code1, project=p1, computer=comp)[0]
    c2 = Calc.objects.get_or_create(title='c2', user=u, type=cat1, status=cas2, code=code1, project=p1, computer=comp)[0]
    c3 = Calc.objects.get_or_create(title='c3', user=u, type=cat2, status=cas1, code=code2, project=p1, computer=comp)[0]
    c4 = Calc.objects.get_or_create(title='c4', user=u, type=cat2, status=cas2, code=code1, project=p2, computer=comp)[0]
    
    cg1 = CalcGroup.objects.get_or_create(title='batch')[0]
        
    ca1 = CalcAttr.objects.get_or_create(title='energy', isnumber=True)[0]
    ca2 = CalcAttr.objects.get_or_create(title='cutoff', isnumber=True)[0]
    ca3 = CalcAttr.objects.get_or_create(title='comment', isnumber=False)[0]
    
#    ca1 = CalcAttr.objects.get_or_create(title='energy')[0]
#    ca2 = CalcAttr.objects.get_or_create(title='comment')[0]
#    ca1.datatype='number'
#    ca1.save()
#    ca2.datatype='string'
#    ca2.save()
    
    e1 = Element.objects.get_or_create(title='H', mass = 1, id=1)
    e2 = Element.objects.get_or_create(title='O', mass = 16, id=8)
    e3 = Element.objects.get_or_create(title='Al', mass = 27, id=13)
    
    #test groups and dependencies
    cg1.calc_set.add(c2,c3,c4)
    c1.in_strucs.add(s1,s2)
    c2.in_strucs.add(s1)
    c3.in_strucs.add(s3)
    c4.in_strucs.add(s4)
    c2.out_strucs.add(s3)
    s3.parents.add(s1,s2)

    print [s.parents.all() for s in s1.children.all()]
    print c1.in_strucs.filter(in_calcs__title__contains='c1')
    
    # test attributes
    # c1.attrs.add(ca1,ca2) #this will not work for intermediate models
    # typical query: find all items where an attribute matches a certain condition
    # s.objects.filter(numattr__title__exact='energy', strucattrnum__val__gt=35)
    # OR
    # attr1 = StrucAttrNum.objects.get(title__exact='energy')
    # attr1.
    # Find all structures for which calculated energy matches a range (clean)
    # Structure.objects.filter(incalcs__numattr__title__exact='energy', incalcs
    
    
    CalcAttrNum.objects.get_or_create(item=c1, attr=ca1, val=-37.4)
    CalcAttrTxt.objects.get_or_create(item=c1, attr=ca3, val='Testing comment')
    CalcAttrNum.objects.get_or_create(item=c1, attr=ca2, val=30)
    CalcAttrNum.objects.get_or_create(item=c3, attr=ca1, val=20)
    CalcAttrNum.objects.get_or_create(item=c4, attr=ca1, val=10)
    CalcAttrNum.objects.get_or_create(item=c4, attr=ca2, val=40)
    
    print c1.attrnum.all()
    
    #test composition
    #print ca1.ncalcs.all()
    
    print ca1.ncalcs.filter(calcattrnum__val__gt=-40)
    print s1.in_calcs.filter(calcattrnum__val__gt=-40).distinct()  #does not specify which attribute!
    print Struc.objects.filter(in_calcs__calcattrnum__val__gt=10).distinct()
    print Struc.objects.filter(in_calcs__calcattrnum__val__gt=10, in_calcs__calcattrnum__attr=ca1).distinct()
    print Struc.objects.filter(in_calcs__calcattrnum__val__gt=10).filter(in_calcs__calcattrnum__attr=ca1).distinct()

InitData()



#p = Person.objects.get(name__contains='Tim')                                                                                       
#print p.car_set.all()
#[c, d] = p.car_set.order_by('title')
#
#print c, c.data
#print d, d.data
#
##c.data['occ'] = '4'
##c.save()
#
#print c.data.keys()
#print Car.objects.filter(data__contains={'engine' : '5.0 L'})
#print '%%%', Person.objects.filter(car__data__contains='occ').distinct()
#qset = Car.objects.filter(data__contains='engine')
#print qset.query
#print qset
#
##print Car.objects.where(HE("data").contains({'engine' : '5.0 L'}))
##print Person..car_set.where(HE("data").contains('occ'))
#
##print d.attribute_set.add(a)   this will not work
#
##Attribute.objects.get_or_create(title='power')
##Attribute.objects.get_or_create(title='wheels')
#a = Attribute.objects.get(title='power')
#b = Attribute.objects.get(title='wheels')
##CarAttribute.objects.get_or_create(car=c, attr=a, value=260)
##CarAttribute.objects.get_or_create(car=d, attr=a, value=200)
##CarAttribute.objects.get_or_create(car=d, attr=b, value=4)
#
#
#print '$$$', c.attribute_set.all()
#print d.attribute_set.all()
#
#print CarAttribute.objects.get(attr=a,car=c).value
##print a.car_set.all()
#print a.car.all()
#
##Give me all cars with power > 210
#print '### wrong', Car.objects.filter(attribute=a, carattribute__value__gt=210)
#print '### wrong', Car.objects.filter(carattribute__value__lt=200)
#print '---', [x.car for x in CarAttribute.objects.filter(attr__title='power',value__lt=300)]
#print '>>>', CarAttribute.objects.filter(attr__title='power',value__lt=300).values('car__title')
#print Car.objects.filter(attribute__title__contains='wheels')
#
#print Person.objects.filter(car__attribute__title__contains='wheels')
#print p.car_set.filter(attribute__title__contains='wheels', )
#
#Vendor.objects.get_or_create(title="Herb")
