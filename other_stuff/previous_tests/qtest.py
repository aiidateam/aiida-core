from newaidajob import *


def Job_test():
    c0 = Calculation.objects.get(id=1118)
    c1 = Calculation.objects.get(id=261)
    print c1.input_structures.all()
    s0 = Structure.objects.get(id=26)
    print s0.in_calculations.all()
    print c1.parent_calcs.all()
    

def Calc_dep_test():
    c0 = Calculation.objects.get(id=261)
    c1 = Calculation.objects.get(id=262)
    c2 = Calculation.objects.get(id=263)

    print c0, c0.parent_calcs.all()
    print c1, c1.parent_calcs.all()
    print c2, c2.parent_calcs.all()

    c2.pk = None
    print "----", c2
    c2.parent_calcs.add(c0)
    c2.parent_calcs.add(c1)
    #c0.parent_calcs.remove(c2) # recursive possible -> watch out!
    print c2.parent_calcs.all()  # all parent calculations
#    print c0.child_calcs.all()  # all dependent calculations
    

def Group_operations():
#---------------- GROUP operations--------------------
    c0 = Calculation.objects.get(id=261)
    c1 = Calculation.objects.get(id=262)
    c2 = Calculation.objects.get(id=263)

    g1=CalculationGroup.objects.get(id=166)
    g2=CalculationGroup.objects.get(id=167)
    
    print g1.members.all()
    print g2.members.all()
    
#    g1.calculation_set.remove(c2)

    print g1.calculation_set.all()
    print g2.calculation_set.all()
    
    print c0.calculationgroup_set.all()
    print c1.calculationgroup_set.all()
    
    print c0.groups.all()
    print c1.groups.all()
    

def Structure_operations():
   #---------------------- Structure connections ---------------------
    s0 = Structure.objects.get(id=1)
   #print s0
    s2 = Structure.objects.get(id=2)
#Structure(formula = 'H2O')
#s2.save()

#sc00=CalculationStructureLink(calculation = c0, structure = s0, connection_type='INPUT')
#sc00.save()
#sc00=CalculationStructureLink.objects.filter(pk=9)[0]
#print sc00

    sc01=CalculationStructureLink(calculation = c0, structure = s0, connection_type='OUTPUT')
    sc02=CalculationStructureLink(calculation = c1, structure = s2, connection_type='INPUT')

    print c0.structures.all()

    sc04=CalculationStructureLink.objects.get(id=27)
    sc04.connection_type='INPUT'
    sc04.save()

#sc01.save()
#sc02.save()
    print sc02


def Composition_test():
    s0 = Structure.objects.get(id=1)
    c = {1:2, 16:1}
    print c
    print c.items()
    print s0
    for pair in c.items():
        comp01 = Composition(structure=s0, element=Element.objects.get(id=pair[0]), quantity=pair[1])
        comp01.save()


def Migrate_calcs():
    calcs = Calculation.objects.all()
    print len(calcs)

    calcs = calcs.exclude(status__title = 'Deleted')
    print len(calcs)
    
    for c in calcs:
        print c.location_perm


def Commit_test():
    c0 = Calculation.objects.get(id=261)
    c0.pk = None
    
    c1 = Calculation.objects.get(id=262)
    c1.pk = None

    c1.parent_calc.add(c0)
    print c1.parent_calc.all()
    print c0.pk, c1.pk


def Attribute_test():
    c0 = Calculation.objects.get(id=261)
    c1 = Calculation.objects.get(id=262)
    c2 = Calculation.objects.get(id=263)
    
    c0.tr = 5
    c1.dep = c0
    print c1.dep

    c0.pk = None
    print c0.user
    c0.user = AuthUser.objects.get(username=getpass.getuser())
    print c0.user
    print c0.id

    class args(object): pass

def Extend_model():
    class MyCalc(Calculation):
        class Meta:
            proxy = True
            app_label = aidadb
        def expos(self):
            print "My id is %s", self.id

    c0 = MyCalc.objects.get(id=261)
    c0.expos()

def Struc_test():
    import pickle
    s = Calculation.objects.get(id=261)
    s.tr = 'hi'
    print Code.objects.get(title='Espresso-4.2.1-pw.x',computer__hostname__exact='palpc170')

def Template_test():
    print sys.argv[0]
    print glob.glob('*py')
    p = {}
    p['hi']=6
    print p    

#--------------------------------------------------------------------------
#Calc_dep_test()
#Group_operations()
#Composition_test()
#Migrate_calcs()
#Commit_test()
#Attribute_test()
#Extend_model()
#Struc_test()
#Template_test()
Job_test()
