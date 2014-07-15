'''
Created on Aug 28, 2013

@author: riki
'''


def Murnaghan_fit(e, v):
    
    import pylab
    import numpy as np
    import scipy.optimize as optimize
    
    e = np.array(e)
    v = np.array(v)
    
    # Fit with parabola for first guess
    a,b,c = pylab.polyfit(v,e,2) 
    
    # Initial parameters
    v0 = -b/(2*a)
    e0 = a*v0**2 + b*v0 + c
    b0 = 2*a*v0
    bP = 4

    def Murnaghan(vol,parameters):
    
        E0 = parameters[0]
        B0 = parameters[1]
        BP = parameters[2]
        V0 = parameters[3]
        
        EM = E0 + B0*vol/BP*( ((V0/vol)**BP)/(BP-1) +1 ) - V0*B0/(BP-1.0)
        
        return EM
    
    # Minimization function
    def residuals(pars,y,x):
        #we will minimize this function
        err =  y - Murnaghan(x,pars)
        return err
    
    p0 = [e0, b0, bP, v0]
    
    return optimize.leastsq(residuals,p0,args=(e,v))
    
      
    
    