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
from matplotlib.pyplot import figure
import pickle

def load_object(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception as ex:
        print("Error during unpickling object (Possibly unsupported):", ex)


def getindex(elem, arr):
    for i in range(len(arr)):
        if str(arr[i])==elem:
            return i
    print('didnt find elem '+elem+' in arr')
    exit
    return -1

def getGeomean(iarr):
    a=np.array(iarr);
    #np.delete(a, 0)
    na=a;
    i=0
    while (i<len(a)):
    #for i in range(len(a)):
        if(a[i]==0):
            na=np.delete(a,[i])
            a=na
        else:
            i=i+1
    return na.prod()**(1.0/len(na))


is2X=True

legend_labels=[]
legend_labels=['1 Core  (8%)','4 Cores (33%)',' 8  Cores (66%)','12 Cores (100%)']


#DDR_ipcs=[]
#d2X_ipcs=[]
#d4X_ipcs=[]
#d5X_ipcs=[]
#C12_gains=[]
C1_gains=[]
C4_gains=[]
C8_gains=[]
C12_gains=[]

appNames = load_object('Workload.pkl')
#C12DDR_ipc = load_object('DDRIPC.pkl')
#C12CXL_ipc = load_object('C4XIPC.pkl')
C1DDR_ipc = load_object('1C.base.nopam.IPC.pkl')
C1CXL_ipc = load_object('1C.4X.50ns.TH70.IPC.pkl')

C4DDR_ipc = load_object('4C.base.nopam.IPC.pkl')
C4CXL_ipc = load_object('4C.4X.50ns.TH70.IPC.pkl')

C8DDR_ipc = load_object('8C.base.nopam.IPC.pkl')
C8CXL_ipc = load_object('8C.4X.50ns.TH70.IPC.pkl')

C12DDR_ipc = load_object('base.nopam.IPC.pkl')
C12CXL_ipc = load_object('4X.50ns.TH70.IPC.pkl')



for i in range(len(C1DDR_ipc)):
    C1ipc_gain = 0
    if(C1DDR_ipc[i]!=0):
        C1ipc_gain = C1CXL_ipc[i]/C1DDR_ipc[i]
    C1_gains.append(C1ipc_gain)

for i in range(len(C4DDR_ipc)):
    C4ipc_gain = 0
    if(C4DDR_ipc[i]!=0):
        C4ipc_gain = C4CXL_ipc[i]/C4DDR_ipc[i]
    C4_gains.append(C4ipc_gain)


for i in range(len(C8DDR_ipc)):
    C8ipc_gain = 0
    if(C8DDR_ipc[i]!=0):
        C8ipc_gain = C8CXL_ipc[i]/C8DDR_ipc[i]
    C8_gains.append(C8ipc_gain)

for i in range(len(C12DDR_ipc)):
    C12ipc_gain = 0
    if(C12DDR_ipc[i]!=0):
        C12ipc_gain = C12CXL_ipc[i]/C12DDR_ipc[i]
    C12_gains.append(C12ipc_gain)

#color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']


matplotlib.rcParams.update({'font.size': 24})


#appNames.append('')
#C12DDR_ipc.append(0)
#C12CXL_ipc.append(0) 
#C8DDR_ipc.append(0)
#C8CXL_ipc.append(0)                
#C12_gains.append(0) 
#C8_gains.append(0)
#
#appNames.append('GeoMean')
#
#GM_C12DDR_ipcs= getGeomean(C12DDR_ipc)
#GM_C12CXL_ipcs= getGeomean(C12CXL_ipc)
#GM_C8DDR_ipcs= getGeomean(C8DDR_ipc)
#GM_C8CXL_ipcs= getGeomean(C8CXL_ipc)
#
#GM_12C_gain = getGeomean(C12_gains)
#GM_8C_gain = getGeomean(C8_gains)
#
#C12_gains.append(GM_12C_gain)
#C8_gains.append(GM_8C_gain)


print('gm perfgain 1C: '+str(C1_gains[len(C1_gains)-1]))
print('gm perfgain 4C: '+str(C4_gains[len(C4_gains)-1]))
print('gm perfgain 8C: '+str(C8_gains[len(C8_gains)-1]))
print('gm perfgain 12C: '+str(C12_gains[len(C12_gains)-1]))
#print('gm perfgain 8C: '+str(GM_C8CXL_ipcs / GM_C8DDR_ipcs))
#print('gm perfgain 12C: '+str(GM_8C_gain))


ifig,iax=plt.subplots()
#iax.set_title(field_names[i])
#X_axis = np.arange(pslen*rblen)
X_axis = np.arange(len(appNames))
#print(str(len(appNames)))
#print(str(len(d2X_gains)))
#print(d2X_gains)

barwidth = 0.18
alval=1
color_list=[ 'lavender', '#bf77be', '#A89AE4','#7C67D6', '#42347E' ]
###plot all bars normalized to DDR
#ddr_bar = iax.bar(X_axis-(barwidth/2), DDR_arrs[ii],edgecolor='black',alpha=alval, color=color_list[0],label='DDR Memory', width=barwidth, zorder=5)
d1X_bar = iax.bar(X_axis-(barwidth*1.5), C1_gains,edgecolor='black',alpha=alval, color=color_list[0],label=legend_labels[0], width=barwidth, zorder=5)
d4X_bar = iax.bar(X_axis-(barwidth*0.5), C4_gains,edgecolor='black',alpha=alval, color=color_list[1],label=legend_labels[1], width=barwidth, zorder=5)
d8X_bar = iax.bar(X_axis+(barwidth*0.5), C8_gains,edgecolor='black',alpha=alval, color=color_list[2],label=legend_labels[2], width=barwidth, zorder=5)
d12X_bar = iax.bar(X_axis+(barwidth*1.5), C12_gains,edgecolor='black',alpha=alval, color=color_list[3],label=legend_labels[3], width=barwidth, zorder=5)

###plotting normalized to 4X
#d2X_bar = iax.bar(X_axis-(barwidth/2), d2X_gains,edgecolor='black',alpha=alval, color=color_list[4],label='2X', width=barwidth, zorder=6)
#d5X_bar = iax.bar(X_axis+(barwidth/2), d5X_gains,edgecolor='black',alpha=alval, color=color_list[7],label='8X', width=barwidth, zorder=5)


#iax.margins(y=0.2)
#print('dummy')
#tmp_count=0
#for p in cxl_bar: ## for main eval
#    height = p.get_height();
#    iax.text(x=p.get_x() - (barwidth), y=height+0.05, s="{}".format(perf_gains[tmp_count]), fontsize=10)
#    tmp_count=tmp_count+1

#for p in ddr_bar: ## for low load
#    height = p.get_height();
#    iax.text(x=p.get_x() + (barwidth/2), y=height+0.05, s="{}".format(perf_gains[tmp_count]), fontsize=10)
#    tmp_count=tmp_count+1
print(appNames[len(appNames)-1])
appNames[len(appNames)-1]='GM_all'
plt.xticks(X_axis, appNames, fontsize=10)
my_yticks=np.arange(0,4,0.5)
plt.yticks(my_yticks)
#iax.set_yticks(np.arange(0, 3, 0.5))
plt.ylim(ymax=3.5)
plt.axhline(y=1, color='black', zorder=5, linestyle=':')
plt.xlim(-1,len(appNames))
#iax.legend(ncol=4,bbox_to_anchor=[0.5,1.15], loc='center')
#iax.legend(ncol=4,bbox_to_anchor=[1,0.9], loc='right', fontsize=15)
iax.legend(ncol=2, loc='best', fontsize=15)

#plt.setp(iax.get_xticklabels(), rotation=35, horizontalalignment='center')
plt.setp(iax.get_xticklabels(), rotation=45, ha='right', fontsize=12)
#ifig.set_size_inches(10,4)
ifig.set_size_inches(20,3)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int)
plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, axis='y', alpha=0.4)
#plt.ylabel('Performance (IPC) Relative to \nCXL baseline(4X)',fontsize=15)
plt.ylabel('Norm. Performance',fontsize=15, labelpad=10)

iax.tick_params(axis='both', which='major', labelsize=15)

ifig.savefig('8C12C_plot.png', bbox_inches='tight')
ifig.savefig('8C12C_plot.pdf', bbox_inches='tight')


    

exit
    
