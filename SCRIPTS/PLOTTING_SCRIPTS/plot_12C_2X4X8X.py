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
legend_labels=['CoaXiaL-2X','CoaXiaL-4X','CoaXiaL-asym']


#DDR_ipcs=[]
#d2X_ipcs=[]
#d4X_ipcs=[]
#d8X_ipcs=[]
d2X_gains=[]
d4X_gains=[]
d8X_gains=[]

appNames = load_object('Workload.pkl')
DDR_ipc = load_object('base.nopam.IPC.pkl')
d2X_ipc = load_object('2X.50ns.TH70.IPC.pkl')
d4X_ipc = load_object('4X.50ns.TH70.IPC.pkl')
d8X_ipc = load_object('8X.50ns.TH70.IPC.pkl')

for i in range(len(DDR_ipc)):
    d2Xipc_gain = 0
    if(DDR_ipc[i]!=0):
        d2Xipc_gain = d2X_ipc[i]/DDR_ipc[i]
    d2X_gains.append(d2Xipc_gain)

for i in range(len(DDR_ipc)):
    d4Xipc_gain = 0
    if(DDR_ipc[i]!=0):
        d4Xipc_gain = d4X_ipc[i]/DDR_ipc[i]
    d4X_gains.append(d4Xipc_gain)

for i in range(len(DDR_ipc)):
    d8Xipc_gain = 0
    if(DDR_ipc[i]!=0):
        d8Xipc_gain = d8X_ipc[i]/DDR_ipc[i]
    d8X_gains.append(d8Xipc_gain)

#toparr = [[[[[] for m in range(cxlen)] for l in range(mclen)] for k in range(ptlen)] for j in range(rblen)]

color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']


matplotlib.rcParams.update({'font.size': 20})


#appNames.append('')
#DDR_ipc.append(0)
#d2X_ipc.append(0) 
#d4X_ipc.append(0)
#d8X_ipc.append(0)                
#d2X_gains.append(0) 
#d4X_gains.append(0)
#d8X_gains.append(0)



#appNames.append('GeoMean')

GM_DDR_ipcs= getGeomean(DDR_ipc)
GM_2X_ipcs= getGeomean(d2X_ipc)
GM_4X_ipcs= getGeomean(d4X_ipc)
GM_8X_ipcs= getGeomean(d8X_ipc)

GM_2X_ipcgain= getGeomean(d2X_gains)
GM_4X_ipcgain= getGeomean(d4X_gains)
GM_8X_ipcgain= getGeomean(d8X_gains)

#d2X_gains.append(GM_2X_ipcs / GM_DDR_ipcs)
#d4X_gains.append(GM_4X_ipcs/GM_DDR_ipcs)
#d8X_gains.append(GM_8X_ipcs/GM_DDR_ipcs)

print('gm perfgain all 2X: '+str(GM_2X_ipcs / GM_DDR_ipcs))
print('gm perfgain all 8x: '+str(GM_8X_ipcs / GM_DDR_ipcs))


ifig,iax=plt.subplots()
#iax.set_title(field_names[i])
#X_axis = np.arange(pslen*rblen)
X_axis = np.arange(len(appNames))
#print(str(len(appNames)))
#print(str(len(d2X_gains)))
#print(d2X_gains)

barwidth = 0.25
alval=1

###plot all bars normalized to DDR
#ddr_bar = iax.bar(X_axis-(barwidth/2), DDR_arrs[ii],edgecolor='black',alpha=alval, color=color_list[0],label='DDR Memory', width=barwidth, zorder=5)
d2X_bar = iax.bar(X_axis-(barwidth), d2X_gains,edgecolor='black',alpha=alval, color=color_list[4],label=legend_labels[0], width=barwidth, zorder=5)
d4X_bar = iax.bar(X_axis, d4X_gains,edgecolor='black',alpha=alval, color=color_list[5],label=legend_labels[1], width=barwidth, zorder=5)
d8X_bar = iax.bar(X_axis+(barwidth), d8X_gains,edgecolor='black',alpha=alval, color=color_list[7],label= legend_labels[2], width=barwidth, zorder=5)

###plotting normalized to 4X
#d2X_bar = iax.bar(X_axis-(barwidth/2), d2X_gains,edgecolor='black',alpha=alval, color=color_list[4],label='2X', width=barwidth, zorder=6)
#d8X_bar = iax.bar(X_axis+(barwidth/2), d8X_gains,edgecolor='black',alpha=alval, color=color_list[7],label='8X', width=barwidth, zorder=5)


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

plt.ylim(ymax=3.7)
tmp_count=0
for p in d8X_bar: ## for main eval
    height = p.get_height();
    if(height>=3.6):
        iax.text(x=p.get_x() - (barwidth), y=height+0.05, s="{}".format(d8X_gains[tmp_count]), fontsize=10)
    tmp_count=tmp_count+1



print(appNames[len(appNames)-1])
appNames[len(appNames)-1]='GM_all'
plt.xticks(X_axis, appNames, fontsize=10)
my_yticks=np.arange(0,4,0.5)
plt.yticks(my_yticks)
#iax.set_yticks(np.arange(0, 3, 0.5))
plt.axhline(y=1, color='black', zorder=5, linestyle=':')

#iax.legend(ncol=3,bbox_to_anchor=[0.5,1.15], loc='center')
iax.legend(ncol=3,bbox_to_anchor=[1,0.9], loc='right', fontsize=15)

#plt.setp(iax.get_xticklabels(), rotation=35, horizontalalignment='center')
plt.setp(iax.get_xticklabels(), rotation=45, ha='right', fontsize=16)
#ifig.set_size_inches(10,4)
#ifig.set_size_inches(20,4) #orig backup 230418
ifig.set_size_inches(20,2.8)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int)
plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, axis='y', alpha=0.4)
#plt.ylabel('Performance (IPC) Relative to \nCXL baseline(4X)',fontsize=15)
plt.ylabel('Norm. Performance',fontsize=16, labelpad=10)

iax.tick_params(axis='both', which='major', labelsize=13)

ifig.savefig('2X8X_plot.png', bbox_inches='tight')
ifig.savefig('2X8X_plot.pdf', bbox_inches='tight')


    

exit
    
