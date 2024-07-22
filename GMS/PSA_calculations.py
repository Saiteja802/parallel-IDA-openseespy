# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 21:58:43 2024

@author: ssi178
"""

import numpy as np
import eqsig.single

gms = 5 # total no of gms whose psuedo acceleration response spectrum should be calculated
T   = np.round(np.arange(0.01,3,0.01),3)    # periods at which psuedo acceleration response should be calculated

DT  = np.genfromtxt('dt.txt')  
PSA = np.zeros([len(T),gms+1])
PSA[:,0] = T
for i in range(gms):
    acc    = np.genfromtxt('gacc_'+str(i+1)+'.txt') 
    record = eqsig.AccSignal(acc, DT[i])
    record.generate_response_spectrum(response_times=T)
    PSA[:,i+1] = record.s_a
    print('Record '+str(i+1)+' completed')

np.savetxt('PSA.txt', PSA)
