from aida.djsite.main.models import *
#from django_orm.postgresql.hstore.expressions import HstoreExpression as HE


cs1 = CodeStatus.objects.get_or_create(title='debug')[0]
cs2 = CodeStatus.objects.get_or_create(title='stable')[0]
ct1 = CodeType.objects.get_or_create(title='espresso')[0]
ct2 = CodeType.objects.get_or_create(title='vasp')[0]
#st1 = StrucType.objects.get_or_create(title='molecule')[0]
#st2 = StrucType.objects.get_or_create(title='crystal')[0]
#    ss1 = StrucStatus.objects.get_or_create(title='icsd')
#    ss2 = StrucStatus.objects.get_or_create(title='generated')
cas1 = CalcStatus.objects.get_or_create(title='finished')[0]
cas2 = CalcStatus.objects.get_or_create(title='running')[0]
cat1 = CalcType.objects.get_or_create(title='relax')[0]
cat2 = CalcType.objects.get_or_create(title='neb')[0]
u = AuthUser.objects.get(username='kyb5pal')
comp = Computer.objects.get_or_create(title='hal', hostname='palhpc.bosch.com', 
                              # ip_address='192.168.0.1', 
                               workdir='/scratch')[0]
q1 = Quality.objects.get_or_create(title='High')[0]

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
c5 = Calc.objects.get_or_create(title='c5', user=u, type=cat2, status=cas2, code=code1, project=p2, computer=comp, quality=q1)[0]

cg1 = CalcGroup.objects.get_or_create(title='batch')[0]
    
ca1 = CalcAttrNum.objects.get_or_create(title='energy')[0]
ca2 = CalcAttrNum.objects.get_or_create(title='cutoff')[0]
ca3 = CalcAttrTxt.objects.get_or_create(title='comment')[0]

e1 = Element.objects.get_or_create(title='H', mass = 1, id=1)
e2 = Element.objects.get_or_create(title='O', mass = 16, id=8)
e3 = Element.objects.get_or_create(title='Al', mass = 27, id=13)

#    ca1 = CalcAttr.objects.get_or_create(title='energy')[0]
#    ca2 = CalcAttr.objects.get_or_create(title='comment')[0]
#    ca1.datatype='number'
#    ca1.save()
#    ca2.datatype='string'
#    ca2.save()
    
    
def GroupTest():
    #test groups and dependencies
    cg1.calc_set.add(c2,c3,c4)
    c1.inpstruc.add(s1,s2)
    c2.inpstruc.add(s1)
    c3.inpstruc.add(s3)
    c4.inpstruc.add(s4)
    c2.outstruc.add(s3)
    s3.parents.add(s1,s2)

    print [s.parents.all() for s in s1.children.all()]
    print c1.inpstruc.filter(inpcalc__title__contains='c1')

def AttrTest():
    # test attributes
    # c1.attrs.add(ca1,ca2) #this will not work for intermediate models
    # typical query: find all items where an attribute matches a certain condition
    # s.objects.filter(numattr__title__exact='energy', strucattrnum__val__gt=35)
    # OR
    # attr1 = StrucAttrNum.objects.get(title__exact='energy')
    # attr1.
    # Find all structures for which calculated energy matches a range (clean)
    # Structure.objects.filter(incalcs__numattr__title__exact='energy', incalcs
    
    
    CalcAttrNumVal.objects.get_or_create(item=c1, attr=ca1, val=-37.4)
    CalcAttrTxtVal.objects.get_or_create(item=c1, attr=ca3, val='Testing comment')
    CalcAttrNumVal.objects.get_or_create(item=c1, attr=ca2, val=30)
    CalcAttrNumVal.objects.get_or_create(item=c3, attr=ca1, val=20)
    CalcAttrNumVal.objects.get_or_create(item=c4, attr=ca1, val=60)
    CalcAttrNumVal.objects.get_or_create(item=c4, attr=ca2, val=40)
    
    
    print c1.attrnum.all()
    
    #test composition
    #print ca1.ncalcs.all()
    
    print ca1.calc_set.filter(calcattrnumval__val__gt=-40)
    print s1.inpcalc.filter(calcattrnumval__val__gt=-40).distinct()  #does not specify which attribute!
    print Struc.objects.filter(inpcalc__calcattrnumval__val__gt=10).distinct()
    
    # list all strctures that were computed with LDA
    print Struc.objects(inpcalc__calcgroup__title__contains="LDA")
    
    print Struc.objects.filter(inpcalc__calcattrnumval__val__gt=10, inpcalc__calcattrnumval__attr=ca1).distinct().query
#SELECT DISTINCT "aidadb_struc"."id", "aidadb_struc"."uuid", "aidadb_struc"."title", "aidadb_struc"."description", "aidadb_struc"."hdata", "aidadb_struc"."jdata", "aidadb_struc"."time", "aidadb_struc"."user_id", "aidadb_struc"."formula", "aidadb_struc"."type_id" FROM "aidadb_struc" INNER JOIN "aidadb_calc_in_strucs" ON ("aidadb_struc"."id" = "aidadb_calc_in_strucs"."struc_id") INNER JOIN "aidadb_calc" ON ("aidadb_calc_in_strucs"."calc_id" = "aidadb_calc"."id") INNER JOIN "aidadb_calcattrnumval" ON ("aidadb_calc"."id" = "aidadb_calcattrnumval"."item_id") WHERE ("aidadb_calcattrnumval"."val" > 10.0  AND "aidadb_calcattrnumval"."attr_id" = 1 )

#   print Struc.objects.filter(in_calcs__calcattrnumval__val__gt=10).filter(in_calcs__calcattrnumval__attr=ca1).distinct()  #this is not what we want
    print CalcAttrNumVal.objects.get(item=c1, attr=ca1).val
    
    print Calc.objects.filter(quality__isnull=False)
    print Calc.objects.filter(quality__title='High')
    for i in range(1000):
        print i, Code.objects.filter(quality__isnull=True) 

def CountTest():
    for i in range(1000):
        print i

#GroupTest()

#

CountTest()
#def Attr(obj, attrtitle, value=None):
#    if obj.type
#    
#    if value:
#        sdf



    
