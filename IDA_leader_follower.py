'Improting the required packages'
from mpi4py import MPI
from mpi_master_slave import Master, Slave
from mpi_master_slave import WorkQueue
import time
import numpy as np
import os
from pathlib import Path
import pandas as pd
'IDA_parllel.py is the file to run time history analysis with a function IDA defined inside'
'make sure the file name is IDA_parllel.py and the function file inside is named as RHA'
from IDA_parallel import IDA
'Run the line below in the command prompt'
# mpiexec -np 5 C:/Users/ssi178/AppData/Local/anaconda3/python.exe  P:/0_parallel_computing_IDA/RHA_master_slave.py
# 2 in the code above is the total number of processors available. Do not use a number greater than the total available processors.
# C:/Users/ssi178/AppData/Local/anaconda3/python.exe is the location where the python interpreter is located in my computer. Use a location specific to your computer here.
# P:/0_parallel_computing_IDA/RHA_master_slave.py is the location where the RHA_master_slave.py is located in my computer.  Use a location specific to your computer here.

'Inputs'
delta_SaT1      = 0.1                                      # intensity increment
maxSaT1         = 0.2                                      # maximum SaT1 in gs
SAscale         = np.arange(delta_SaT1,maxSaT1,delta_SaT1) # array of SaT1 values for scaling
SAscale         = np.round(SAscale,4)                      # rounding all the values off to 4 decimal places
gms             = 5                                        # total number of ground motions for each intensity level
dlim            = 10                                       # drift limit (%) to terminate analysis the analysis. This is representative of structural collapse
ntrials         = 0                                        # ntrials+1 is the number of times bisection is performed to obtain a precise estimate of the collapse intensity                         
curdir          = 'P:/0_parallel_computing_IDA/'           # location of the current directory in which the python files are placed

def IDA_saveloc(curdir,gmno,SAscaled): # location to save IDA results. Change this based on your preference
    return curdir+'IDA_results/GM_'+str(gmno)+'/'+str('{:.4f}'.format(round(SAscaled,4)))+'g' 
def GM_loc(curdir): # location of the ground motions. Change this based on your preference
    return curdir+'GMS'

def main():  
    name = MPI.Get_processor_name()
    rank = MPI.COMM_WORLD.Get_rank()
    size = MPI.COMM_WORLD.Get_size()
    if rank == 0: # Master
        begin = time.time()
        app = MyApp(slaves = range(1, size))
        app.run(SAscale, gms,delta_SaT1,dlim,ntrials)
        app.terminate_slaves()
        end = time.time()
        print(f"Total runtime of the program is {(end - begin)/60/60} hours")
    else: # Any slave
        MySlave().run()
    
class MyApp(object):
    """
    This is my application that has a lot of work to do so it gives work to do
    to its slaves until all the work is done
    """
    def __init__(self, slaves):
        # when creating the Master we tell it what slaves it can handle
        self.master = Master(slaves)
        # WorkQueue is a convenient class that run slaves on a tasks queue
        self.work_queue = WorkQueue(self.master)
    def terminate_slaves(self):
        """
        Call this to make all slaves exit their run loop
        """
        self.master.terminate_slaves()
    def run(self, SAscale, gms,delta_SaT1,dlim,ntrials):
        """
        This is the core of my application, keep starting slaves
        as long as there is work to do
        """
        #
        # let's prepare our work queue. This can be built at initialization time
        # but it can also be added later as more work become available
        for z in range(0,len(SAscale)):
            for k in range (1,gms+1):
                self.work_queue.add_work(data = (k,SAscale[z],delta_SaT1,dlim,ntrials,str(IDA_saveloc(curdir,k,SAscale[z])),str(GM_loc(curdir))))       
        # Keeep starting slaves as long as there is work to do
        while not self.work_queue.done():
            # give more work to do to each idle slave (if any)
            self.work_queue.do_work()
            # reclaim returned data from completed slaves
            for slave_return_data in self.work_queue.get_completed_work():
                done, message, rankno = slave_return_data
                if done:                    
                    print('Processor "%d" - "%s"' % ( rankno, message) )
            # sleep some time
            time.sleep(0)

class MySlave(Slave):
    """
    A slave process extends Slave class, overrides the 'do_work' method
    and calls 'Slave.run'. The Master will do the rest
    """
    def __init__(self):
        super(MySlave, self).__init__()
    def do_work(self, data):
        rank = MPI.COMM_WORLD.Get_rank()
        name = MPI.Get_processor_name()
        gmno, SAscaled,delta_SaT1,dlim,ntrials,saveloc,gmloc = data # read data from the master
        # gmno is the ground the current ground motion number
        # SAscaled is the target value to which Sa(T1) of the current GM should be scaled
        # gmloc is the location of the ground motions
        # saveloc is the location to save the results of the current ground motion (gmno) scaled to intensity level equal to SAscaled 
        if not os.path.exists(saveloc):
            os.makedirs(saveloc)         # create directory if it doesnt exist  
        file_list = os.listdir(os.path.dirname(saveloc))  # get file list of intensities for a specific gm (moved back by one directory)   
        for zdummy in range(0,len(file_list)):      # Loop through all intensities to check: 1) if any previous analysis exists 2) If it does, did collapse occur?  
            outputloc   = os.path.dirname(saveloc)+'/'+file_list[zdummy]+'/output.txt' # Path of the analysis output file 
            if Path(outputloc).is_file(): # check if output file exists
                outputmessage = pd.read_csv(outputloc) 
                if 'Drift > '+str(dlim) in str(outputmessage.iloc[0][0]):  
                    collapse = 'true'              # set collapse flag as true if the strucutre has collapsed 
                    break
                else:
                   collapse = 'false'              # set collapse flag as false if the strucutre has not collapsed  
            else:
                collapse = 'false'                 # set collapse flag as false as no analysis file has been detected. It either means the analysis was not started or stopped before it was completed
        if len(file_list) == 0:                    # set collapse flag as false if no analysis files have been found. (no previous analysis history exists) 
               collapse = 'false'                          
        if  collapse != 'true':                 # run a specific model with a specific gmno and intensity if collapse is not true                                                   
            maxdri_IDA = IDA(dlim,gmno,SAscaled,saveloc,gmloc) # running response history analysis of ground motion no: gmno at Sa(T1)= SAscaled 
            'Bisection algorithm is performed for ntrials+1 number of times to estimate the collapse intensity with finer precision'
            if maxdri_IDA > dlim:  
                'first bisection to reduce the previous intensity increment by half, if collapse has been observed'
                delx = 2
                SAscaled   = np.round(SAscaled - delta_SaT1/delx ,4) ; delx         = delx*2
                saveloc    = str(IDA_saveloc(curdir,gmno,SAscaled))
                if not os.path.exists(saveloc):
                    os.makedirs(saveloc)         # create directory if it doesnt exist  
                maxdri_IDA = IDA(dlim,gmno,SAscaled,saveloc,gmloc)
                for trial in range(0,ntrials):
                    if maxdri_IDA > dlim:
                        'Next bisection to reduce the previous intensity increment by half again, if collapse has been observed'
                        SAscaled   = np.round(SAscaled - delta_SaT1/delx ,4);delx         = delx*2
                        saveloc    = str(IDA_saveloc(curdir,gmno,SAscaled))
                        if not os.path.exists(saveloc):
                            os.makedirs(saveloc)         # create directory if it doesnt exist  
                        maxdri_IDA = IDA(dlim,gmno,SAscaled,saveloc,gmloc)
                    else:
                        'Next bisection to increase the previous intensity increment by half again, if collapse has not been observed'
                        SAscaled   = np.round(SAscaled + delta_SaT1/delx ,4);delx         = delx*2   
                        saveloc    = str(IDA_saveloc(curdir,gmno,SAscaled))
                        if not os.path.exists(saveloc):
                            os.makedirs(saveloc)         # create directory if it doesnt exist  
                        maxdri_IDA = IDA(dlim,gmno,SAscaled,saveloc,gmloc)                       
        return (True, 'Completed ground motion '+str(gmno)+' at level '+str(round(SAscaled,4))+'g',rank)


if __name__ == "__main__":
    main()