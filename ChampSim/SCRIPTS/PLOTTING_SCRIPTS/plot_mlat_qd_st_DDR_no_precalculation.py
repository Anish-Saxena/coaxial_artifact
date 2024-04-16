#!/usr/bin/env python3

import os
import sys
import csv
import math
import statistics
import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['agg.path.chunksize'] = 10000
import matplotlib.pyplot as plt 
import pickle
import argparse

from matplotlib.pyplot import figure

def load_object(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception as ex:
        print("Error during unpickling object (Possibly unsupported):", ex)

def getGeomean(iarr):
    a=np.array(iarr);
    return a.prod()**(1.0/len(a))



def getindex(elem, arr):
    for i in range(len(arr)):
        if str(arr[i])==elem:
            return i
    print('didnt find elem '+elem+' in arr')
    exit
    return -1

cxl_delay = 60

#appNames=[]
#
#DDR_mbws=[]
#DDR_mlats=[]
#lowload_mlats=[]
#dummy_for_MBW_label=[]

ddr5_BW = 38.4



#color_list[getindex('ideal',partitions)][getindex('clean',ddio_setups)] ='#C26989'
color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']

appNames = load_object('Workload.pkl')
#DDR_mbws = load_object('DDRBW.pkl')
#DDR_mlats= load_object('DDRLAT.pkl')
DDR_mbws = load_object('base.nopam.BW.pkl')
DDR_mlats= load_object('DDR_LLCLAT.pkl')
DDR_mlats=[x/2.4 for x in DDR_mlats]

len_without_means=len(appNames)-6
appNames=appNames[:len_without_means]
DDR_mbws=DDR_mbws[:len_without_means]
DDR_mlats=DDR_mlats[:len_without_means]


print(appNames)
num_apps = len(appNames)

DDR_onchip_delay = [26] * num_apps # PAM is off for baseline, so ratio is 0
lowload_mlats = [40.0] * num_apps
for i in range(len(DDR_mlats)):
    if(DDR_mlats[i]==0):
        lowload_mlats[i]=0;
        DDR_onchip_delay[i]=0;
    else:
        DDR_mlats[i]=DDR_mlats[i]+17


DDR_mbws = [x*100/ddr5_BW for x in DDR_mbws]
#DDR_mlats = [x/2.4 for x in DDR_mlats]

fs_smalltext=12

matplotlib.rcParams.update({'font.size': 12})

################# PLOT latency breakdown ##################3

#ifig,iax=plt.subplots()
ifig,(iax1,iax2)=plt.subplots(2)
#iax2=iax.twinx()
#iax.set_title(field_names[i])
#X_axis = np.arange(pslen*rblen)
X_axis = np.arange(len(appNames))

barwidth = 0.5
alval=1
iax1.bar(X_axis, DDR_mlats,edgecolor='black',alpha=alval, color='lavender',label='Queuing Delay', width=barwidth, zorder=4)
iax1.bar(X_axis, lowload_mlats,edgecolor='black',alpha=alval, color='indigo',label='Access Service Time', width=barwidth, zorder=5)

iax1.bar(X_axis, DDR_onchip_delay,edgecolor='black',alpha=alval, color='#FFA500',label='On-chip Time', width=barwidth, zorder=5, bottom = lowload_mlats)
for i in range(len(DDR_mlats)):
    if(DDR_mlats[i] >520):
        iax1.text(i,525,str(int(DDR_mlats[i])),zorder=5,fontsize=10, ha='center', rotation=50)


#plt.xticks(X_axis, appNames, fontsize=10)
#iax1.legend(ncol=3,bbox_to_anchor=[0.5,1.3], loc='center', fontsize=16)
#iax1.legend(ncol=1,bbox_to_anchor=[1,0.9], loc='right', fontsize=16)
iax1.legend(ncol=3,loc='best')
iax1.set_xticks([], [])
#iax1.set_ylabel('Average Memory\nAccess Latency (ns)')
iax1.set_ylabel('Average L2C Miss\n Latency (ns)')
#iax1.set_ylim(0,200)
iax1.set_ylim(0,530)
major_ticks2 = np.arange(0, 550, 100)
iax1.set_yticks(major_ticks2)

plt.xlim(-1,len(appNames))
iax1.set_xlim(-1,len(appNames))
#iax1.text(-0.5,202,'356ns',zorder=5, fontsize=10)

#plt.setp(iax1.get_xticklabels(), rotation=45, ha='right', fontsize=13)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1)
iax1.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, axis='y', alpha=0.3)

#for i in range(len(DDR_mlats)-1): #skip geomean, we'll handle it separately
#    if(DDR_mlats[i]>400):
#        iax1.text(i,400,str(round(DDR_mlats[i],0)),zorder=5, fontsize=fs_smalltext, ha='center')


################# PLOT MBW ##################3

#ifig,iax=plt.subplots()
#iax.set_title(field_names[i])
#X_axis = np.arange(pslen*rblen)
X_axis = np.arange(len(appNames))

barwidth = 0.5
alval=1
iax2.bar(X_axis, DDR_mbws,edgecolor='black',alpha=alval,label='MBW Utilization', width=barwidth, zorder=5, color='cornflowerblue')
#iax2.bar(X_axis, DDR_mbws,edgecolor='black',alpha=alval,label='MBW Utilization', width=barwidth, zorder=5, color='cornflowerblue')

#iax3=iax2.twinx()
#iax3.set_ylabel('Memory Bandwidth\nUtilization')
iax2.set_ylabel('Memory Bandwidth\nUtilization')
#iax.set_ylabel('Memory Bandwidth Utilization')
#iax.set_ylim(0,200)
#iax.text(-0.5,201,'356ns',zorder=5, fontsize=10)

#plt.setp(iax.get_xticklabels(), rotation=35, horizontalalignment='center')
plt.xticks(X_axis, appNames)
plt.setp(iax2.get_xticklabels(), rotation=52, ha='right', fontsize=10)
dx = 0.1; dy = 0.05 
offset = matplotlib.transforms.ScaledTranslation(dx, dy, ifig.dpi_scale_trans) 
plt.xlim(-1,len(appNames))
iax2.set_xlim(-1,len(appNames))
#iax2.xlim(-1,len(appNames))
ifig.set_size_inches(10,4)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, alpha=0.3)
iax2.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, axis='y', alpha=0.3)
#plt.ylabel(fields[ii])



#ifig.savefig('all_apps_mbw_DDR.png', bbox_inches='tight')
ifig.savefig('mlat_bd_and_mbw_DDR.png', bbox_inches='tight')
ifig.savefig('mlat_bd_and_mbw_DDR.pdf', bbox_inches='tight')




exit
    
