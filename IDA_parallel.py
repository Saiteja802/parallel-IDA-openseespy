from openseespy.opensees import *
import numpy as np

def IDA(dlim,gmno,Sa_scaled,saveloc,GMloc): 
    wipe() # wipe previously existing models
    from Canti2DEQ import cantilever_model    # read the building model. Using the first earthquake example from OpenSeespy website. Replace with your building model
    cntrl_nodes, T1, bh = cantilever_model()  #  Run the building model with gravity load and damping applied. Set the analysis time to 0.                     
    # cntrl_nodes = list of nodes at which dispalcement and acceleration response histories are recorded (from the bottom most node that fixed to the topmost node)
    # T1 is the fundamental period of the structure required to read the PSA value corresponding to T1
    # bh is the list of heights of each storey starting from the bottom to the top
    print ("################################################")
    print("Starting RHA of cantilever column - intensity level - "+str(Sa_scaled)+'g'+" Ground motion no. - "+str(gmno))
    print ("################################################")
    ts     = np.genfromtxt(GMloc+'/DT.txt')                                # time step of the GMs
    gacc   = np.genfromtxt(GMloc+'/gacc_'+str(gmno)+'.txt')                # gacc data 
    dt     = ts[gmno-1]                                                    # time step of the GM
    pSA    = np.genfromtxt(GMloc+'/PSA.txt')    # importing response spectra of GMs. Note that the units of Psa are inch/sec^2
    psagm  = pSA[np.argmax(pSA[:,0]>= T1),gmno] # Sa(T1)  
    scale_factor  = (Sa_scaled*9.81*100/2.54)/psagm   # GM scale factor. Sa_scaled in g's is first converted to inch/sec^2 and then the scale factor required to scale the GM to have Sa(T1) = Sa_scaled is calculated   
    timeSeries('Path',3,'-dt',dt,'-values',*gacc,'-factor',scale_factor)   # time series scaled by scale_factor
    pattern('UniformExcitation', 3, 1,'-accel', 3)  # acc loading pattern 
    'Displacement and acceleration response recorders'
    recorder('Node', '-file', saveloc+"/displacement."+str(gmno)+".out", '-time', '-node'  ,*cntrl_nodes, '-dof',1,'disp')  # dispalcement recorder. Replace with the node numbers and dof of interest based on your model
    recorder('Node', '-file', saveloc+"/acceleration."+str(gmno)+".out",'-timeSeries',3,'-time','-node',*cntrl_nodes,'-dof',1,'accel') # acceleration recorder. Replace with the node numbers and dof of interest based on your model
    wipeAnalysis()		  # clear previously-define analysis parameters    
    # analysis parameters
    system('BandGeneral') # how to store and solve the system of equations in the analysis
    constraints('Plain')  # how it handles boundary conditions
    numberer('Plain')     # Use RCM if the model is complex. This scheme will renumber dof's to minimize stiffness matrix band-width
    algorithm('Linear')	  # use Linear algorithm for linear analysis. DO NOT USE LINEAR ALGORITHM FOR NONLINEAR PROBLEMS
    test('NormUnbalance', 1.0e-3, 500, 0, 0)
    integrator('Newmark',0.5,0.25) # using the newmark's average acceleration scheme (implicit scheme)
    analysis('Transient') # define type of analysis: time-dependent
    drix = np.zeros(len(cntrl_nodes)-1)   # array to track the peak inter-storey drift ratio along the model height
    for istr in range(len(cntrl_nodes)-1):
        globals()["drift_S_"+str(istr)]   = [] # variables to track the inter-storey  drift ratio history at each level
    for i in range(len(gacc)):
        analyze(1, dt)	  # Run the analysis at a constant time step dt
        for istr in range(0,len(drix)):   # loop across different levels of the model
            disp   = nodeDisp(cntrl_nodes[istr])     # displacement at the bottom node of storey istr
            disp1  = nodeDisp(cntrl_nodes[istr+1])   # displacement at the top node of storey istr
            globals()["drift_S_"+str(istr)].append(abs(disp1[0]-disp[0])/bh[istr]*100)   # inter-storey  drift ratio history (%) at storey istr
            drix[istr] = max(globals()["drift_S_"+str(istr)]) # peak inter-storey  drift ratio (%) at storey istr until the current step
        if max(drix) > dlim: # condition to stop the analysis if the collapse criterion is met (max inter-storey drift ratio > limit)
            print('Gm: '+str(gmno)+' collapsed at '+str(Sa_scaled)+' g') # message to print the collapse intensity of ground motion no. gmno
            # np.savetxt('collapse.txt', ["Analysis terminated as Drift > "+str(dlim)])
            with open(saveloc+"/output.txt", "w") as file:
                file.write("Analysis terminated as inter-storey drift ratio > "+str(dlim))
            break
    maxdri_IDA = max(drix) # max inter-storey along the building height for ground motion no. gmno at Sa(T1) of Sa_scaled
    with open(saveloc+"/output.txt", "w") as file:
        file.write("Analysis completed")
    wipe()
    return maxdri_IDA # return max inter-storey drift ratio



# gmno = 1
# Sa_scaled = 0.1
# saveloc   = 'P:/0_parallel_computing_IDA/'+ 'IDA_results/'+str(Sa_scaled)+'g'
# GMloc     = 'P:/0_parallel_computing_IDA/GMS'
# ns =1
# dlim = 0.001
# level = 0.1
# maxdri_IDA = IDA(1,0.001,1,level,'P:/0_parallel_computing_IDA/'+ 'IDA_results/'+str(level)+'g','P:/0_parallel_computing_IDA/'+ 'GMS')




