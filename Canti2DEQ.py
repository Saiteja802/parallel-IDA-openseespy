print("=========================================================")
print("Start cantilever 2D EQ ground motion with gravity example")

from openseespy.opensees import *
import numpy as np

def cantilever_model():
    # --------------------------------------------------------------------------------------------------
    # Example 1. cantilever 2D
    # EQ ground motion with gravity
    # all units are in kip, inch, second
    # elasticBeamColumn ELEMENT
    #		Silvia Mazzoni & Frank McKenna, 2006
    #
    #    ^Y
    #    |
    #    2       __ 
    #    |         | 
    #    |         | 
    #    |         | 
    #  (1)      36'
    #    |         | 
    #    |         | 
    #    |         | 
    #  =1=    ----  -------->X
    #
    
    # SET UP ----------------------------------------------------------------------------
    wipe()						       # clear opensees model
    model('basic', '-ndm', 2, '-ndf', 3)	       # 2 dimensions, 3 dof per node
    # file mkdir data 				   # create data directory
    
    # define GEOMETRY -------------------------------------------------------------
    # nodal coordinates:
    node(1, 0., 0.)					   # node#, X Y
    node(2, 0., 432.)
    
    # Single point constraints -- Boundary Conditions
    fix(1, 1, 1, 1) 			           # node DX DY RZ
    
    # nodal masses:
    mass(2, 5.18, 0., 0.)			   # node#, Mx My Mz, Mass=Weight/g.
    
    # Define ELEMENTS -------------------------------------------------------------
    # define geometric transformation: performs a linear geometric transformation of beam stiffness and resisting force from the basic system to the global-coordinate system
    geomTransf('Linear', 1)  		       # associate a tag to transformation
    
    # connectivity:
    element('elasticBeamColumn', 1, 1, 2, 3600.0, 3225.0,1080000.0, 1)	
    
    # define GRAVITY -------------------------------------------------------------
    timeSeries('Linear', 1)
    pattern('Plain', 1, 1,)
    load(2, 0., -2000., 0.)			    # node#, FX FY MZ --  superstructure-weight
    
    constraints('Plain')  				# how it handles boundary conditions
    numberer('Plain')			    # renumber dof's to minimize band-width (optimization), if you want to
    system('BandGeneral')		    # how to store and solve the system of equations in the analysis
    algorithm('Linear')                 # use Linear algorithm for linear analysis
    integrator('LoadControl', 0.1)			# determine the next time step for an analysis, # apply gravity in 10 steps
    analysis('Static')					    # define type of analysis static or transient
    analyze(10)					        # perform gravity analysis
    loadConst('-time', 0.0)				# hold gravity constant and restart time
    
    
    # set damping based on first eigen mode
    freq = eigen('-fullGenLapack', 1)[0]**0.5
    T1   = 2*np.pi/freq
    dampRatio = 0.02
    rayleigh(0., 0., 0., 2*dampRatio/freq)
    return [1,2], round(T1,2), [432.]
    
    

