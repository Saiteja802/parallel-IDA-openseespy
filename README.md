Please cite the following article if you are using this code: 'Sistla S, Chandramohan R, Sullivan TJ. Loss-oriented hazard-consistent incremental dynamic analysis. Structural Safety. 2026 Jan 28;102692.'

General Notes: Incremental dynamic analysis using OpenSeespy and leader-follower architecture
This document is intended to help users interested in conducting incremental dynamic analysis (IDA) using parallel computing. The example code (IDA_leader_follower.py) can be used to conduct IDA of a building model using the leader-follower architecture to efficiently run analysis in parallel. 
The following packages are to be installed before running the main file (IDA_leader_follower.py) in the command line:
1. Install mpiexec using the following link
	* https://learn.microsoft.com/en-us/message-passing-interface/microsoft-mpi?redirectedfrom=MSDN#ms-mpi-source-code
	* use msmpisetup.exe and not .msi extension
2. Install Openseespy and python packages for parallel computing (py-3.8 – m implies python version 3.8. Replace with whatever version is installed on your PC).
	* py -3.8 -m pip install openseespy
	* py -3.8 -m pip install mpi4py
	* py -3.8 -m pip install mpi_master_slave
Note1: Message Passing Interface (MPI) is a standardized and portable way for computers to communicate with each other when working together on a task. pip install mpi4py installs this package for python. 
Note2: Leader-follower architecture is a sort of a centralized load balancing scheme to efficiently improve the efficiency of parallel computing. mpi_master_slave installs this package for python. This package was previously developed by Luca Scarabello, Landon T. Clipp (https://github.com/luca-s/mpi-master-slave). It has been modified to run MSA using OpenSeespy. Details of this package and some example applications are in the original GitHub page. More basic information about the master-slave architecture can be found at: 
  *	https://www.geeksforgeeks.org/master-slave-architecture/ 
  *	https://medium.com/@cpsupriya31/understanding-master-slave-architecture-uses-and-challenges-2acc907de7c4

Instrcutions to use the code:
1. Prepare the required files to conduct MSA using your model. The required files are:
	* Canti2DEQ.py 
		* This is an example linear elastic cantilever example from the OpenSeespy website (https://openseespydoc.readthedocs.io/en/latest/src/Canti2DEQ.html). 
		* Replace this with your building model, with the gravity load  and damping applied. 
		* return a list of: 
			* nodes (cntrl_nodes) at which the displacement and acceleration time histories are supposed to be recorded.
			* Fundamental period of the building (T1)
			* List of heights of each storey starting from the bottom 
	* IDA_parallel.py
		* This file has the commands to conduct response history analysis of your building subjected to a ground motion time history.
		* inputs to this file are the drimit limit for collapse (dlim), intensity level (g) to which the PSA of the ground motion should be scaled (Sa_scaled) ground motion number (gmno), and the folder to save the IDA results (saveloc), location where the         GMs for IDA are located in (GMloc). The results include displacement and acceleration response histories at the cantilever tip. The files to be saved can be modified based on your preference.
	* IDA_leader_follower.py
		* This file employs the leader-follower architecture to coduct IDA of your model in parallel.
	Additional codes:
	* PSA_calculations.py, placed within GMS folder, is a code to compute PSA of your ground motion set.
2. Details about IDA_parallel.py:
	* The building model defined in Canti2DEQ.py file is imported in line 6 and 7.
	* Example ground motions are placed in the folder GMS. Inside the GMS folder,  are 5 sample ground motions and also the respective recording time steps of the ground motions are in the file named DT. The acceleration data is in incg/sec^2 (as the example cantilevel model uses inches as the units for length). Replace these files based on your intensity levels and the ground motions selected at these levels. Make sure the acceleration and DT file formats are similar to the ones in this example.
	* Based on the gmno and GMloc inputs, the time step and ground acceleration data are loaded in lines 14, 15, 16.
	* The PSA of the ground motions, stored as 'PSA.txt' in the GMS folder is imported in line 17. PSA_calculations.py, placed within GMS folder, is a code to compute PSA of your ground motion set.
	* scale_factor, calculated in line 18, is the factor to scale the Sa(T1) of the current GM to the Sa_scaled value. Note that this scale factor computation is wrt PSA units of g, while the model and GM units are 	   inches.
	* Based on the specified cntrl_nodes (from cantilever_model), acceleration and displacement time histories are recorded in lines 23 and 24. Here is a good place to add any additional recorders based                         	   on your requirements.
	* Change the analysis parameters based on your requirements. DO NOT USE LINEAR ALGORITHM FOR NONLINEAR ANALYSIS USING IMPLICIT SCHEMES.
	* Code to track the peak inter-storey drift ratio throughout the analysis is placed between lines 35 and 53. This information is used in the IDA_leader_follower.py to prevent running analyses that are not 	    necessary (intensity levels beyond collapse)
		* If the peak SDR exceeds the dlim specified, the analysis is terminated as the structure has collapsed and an output file shall be written to the saveloc with the message: "Analysis terminated as 			    inter-storey drift ratio > "+str(dlim). 
		* If the analysis completes without structural collapse, an output file shall be written to the saveloc with the message: "Analysis completed"


3. Details about IDA_leader_follower.py: 
	* IDA_parallel.py file is loaded and the function RHA is imported in line 12.
	* Line 20 to 27 are the required inputs. 
	* IDA_saveloc (line 29) returns the directory where the GMS are placed. Replace based on your requirements (or just use this format)
	*  GM_loc (line 31) returns the directory where the IDA results will be saved.
4. Note: Read through https://github.com/luca-s/mpi-master-slave to understand the functioning of the leader-follower algorithm.
	* Inputs to the leader processor (rank == 0) are provided in line 41.
	* Same inputs to the leader processor are again provided in line 63.
	* The list of jobs are created in line 73. Modify this based on your requirements (i.e. if you want to run multiple models)
	* The inputs to each follower processor are provided by the leader in line 96.
	* The directory to save IDA results is created in lines 101 to 103.
	* Lines 104 to 117 determine if structural collapse has occured. If yes, the collapse flage is 'True, if not, it is 'False'.
	* Call in the IDA function file to provide the inputs and start a response history analysis (line 120).
	* Line 119 to 142 applies the bisection algorrithm to obtain a precise estimate of the collapse intensity. Adjust the variable ntrials based on the required precision. (ntrails = 1 would be sufficient as ntrials+1 	   number of bisections are conducted by this code)

5. RUN PARALLEL IDA USING OPENSEESPY
Run the IDA_leader_follower.py in the command line using the command below:
	*  mpiexec -np 2 C:/Users/ssi178/AppData/Local/anaconda3/python.exe  P:/0_parallel_computing_MSA/IDA_leader_follower.py
		* 2 in the code above is the total number of processors available. Do not use a number greater than the total available processors.
		* C:/Users/ssi178/AppData/Local/anaconda3/python.exe is the location where the python interpreter is located in my computer. Use a location specific to your computer here.
		* P:/0_parallel_computing_IDA/IDA_leader_follower.py is the location where the IDA_leader_follower.py is located in my computer.  Use a location specific to your computer here.
