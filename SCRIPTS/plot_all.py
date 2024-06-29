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

import argparse

from matplotlib.pyplot import figure
import pickle

def load_object(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception as ex:
        print("Error during unpickling object (Possibly unsupported):", ex)


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


def getindex(elem, arr):
    for i in range(len(arr)):
        if str(arr[i])==elem:
            return i
    print('didnt find elem '+elem+' in arr')
    exit
    return -1


cxl_delay = 25

ipc_gains=[]
sa_ipc_gains=[]
sp_ipc_gains=[]

dummy_for_MBW_label=[]

ddr5_BW = 38.4



appNames = load_object('app.pkl')
DDR_mbws = load_object('DDRBW.pkl')

DDR_mlats= load_object('DDRLAT.pkl')
CXL_mbws = load_object('CXLBW.pkl')

CXL_mlats= load_object('CXLLAT.pkl')
DDR_ipc = load_object('DDRIPC.pkl')
CXL_ipc = load_object('CXLIPC.pkl')
#ipc_gains = load_object('speedup.pkl')
ipc_gains = [CXL_ipc[i] / DDR_ipc[i] for i in range(len(DDR_ipc))]
mean_speedup = getGeomean(ipc_gains);
print("mean_speedup: "+str(mean_speedup))

appNames_ipc=appNames


DDR_mlats=[x/2.4 for x in DDR_mlats]
CXL_mlats=[x/2.4 for x in CXL_mlats]

print(DDR_mlats)

print(appNames)
num_apps = len(appNames)


color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']


################# PLOT latency breakdown ##################3

### overlapping mlat with low lowad lat makes the plot fat...
#DDR_QD =[]

print(str(len(appNames)))


ylabel_size=15
fs1=10;
fs_smalltext=12;
#fs_smalltext=10;
fs_legend=15;
fs_ytick=14;
fs_xtick=16
matplotlib.rcParams.update({'font.size': fs1})
ifig = plt.figure(figsize=(20, 9)) #### backup, original size
#ifig = plt.figure(figsize=(20, 8.5))

### grid space to something like (3, elements_in_ipc_gains+1)
#grid = plt.GridSpec(3, len(ipc_gains)+1, wspace=1, hspace=0.1)
grid = plt.GridSpec(3, len(ipc_gains)+1, wspace=0, hspace=0.1)


#### looks like col width can be set to number of elements (+2 for ipc, cuz blank and geomean)
iax0=plt.subplot(grid[0, 0:len(ipc_gains)])
iax1=plt.subplot(grid[1, 0:len(DDR_mbws)])
iax2=plt.subplot(grid[2, 0:len(DDR_mbws)])

iax0.margins(x=0.02)
iax1.margins(x=0.02)
iax2.margins(x=0.02)

iax0.text((len(ipc_gains)-1)/2,2.9,(f"GeoMean: {mean_speedup:.2f}"),zorder=5, fontsize=fs_smalltext, ha='center');
mean_range_begin = len(appNames_ipc) - 5
mean_range_end = len(appNames_ipc)



##### plot IPC gains
X_axis = np.arange(len(appNames))
X_axis_ipc = np.arange(len(appNames_ipc))
barwidth = 0.5
alval=1
iax0.bar(X_axis_ipc, ipc_gains, edgecolor='black', alpha=alval, color=color_list[5], width=barwidth, zorder=5)

iax0.axhline(y=1, color='black', linestyle='--',zorder=5)
#if(max(ipc_gains) > 2):
iax0.set_ylim(ymax=3.2)

for i in range(len(ipc_gains)-1): #skip geomean, we'll handle it separately
    if(ipc_gains[i]>3.5):
        iax0.text(i,3.52,str(round(ipc_gains[i],1)),zorder=5, fontsize=fs_smalltext, ha='center')



props = dict(boxstyle='round', facecolor=color_list[4], alpha=0.5)

iax0.set_xticks([], [])
iax0.set_ylabel('Normalized\nPerformance', fontsize=ylabel_size)
iax0.tick_params(axis='y', which='major', labelsize=fs_ytick)
major_ticks = np.arange(0, 3.3, 0.5)
iax0.set_yticks(major_ticks)
iax0.grid(color='gray', linestyle='--', linewidth=0.2, markevery=float, zorder=1, alpha=0.4)


##### plot mlat breakdown for qd and st

X_axis = np.arange(len(appNames))
print(str(len(X_axis)))
#print(str(len(lowload_mlats)))

onchip_color = '#FFA500'

barwidth = 0.3
alval=1
iax1.bar(X_axis-(barwidth*0.55), DDR_mlats,edgecolor='black',hatch='//',alpha=0.7, color='indigo', width=barwidth, zorder=5, label='Baseline')

iax1.bar(X_axis+(barwidth*0.55), CXL_mlats,edgecolor='black',alpha=alval, color='indigo', width=barwidth, zorder=5, label='CoaXiaL',) #redundant, no label, use same color



iax1.tick_params(axis='y', which='major', labelsize=fs_ytick)

iax1.legend(ncol=4,loc='best',fontsize=fs_legend)
iax1.set_xticks([], [])
iax1.set_ylabel('Average Memory \nAccess Latency (ns)', fontsize=ylabel_size)
iax1.set_ylim(0,410)


plt.yticks(fontsize=fs_ytick)

iax1.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, alpha=0.4)




################# PLOT MBW ##################3

X_axis = np.arange(len(appNames))

legend_dummy=[]
legend_dummy2=[]
for i in range(len(appNames)):
    legend_dummy.append(0)
    legend_dummy2.append(0)

alval=1
iax2.bar(X_axis-(barwidth*0.55), DDR_mbws,edgecolor='black',hatch='//',alpha=alval, width=barwidth, zorder=5, color='cornflowerblue')
iax2.bar(X_axis+(barwidth*0.55), CXL_mbws,edgecolor='black',alpha=alval, width=barwidth, zorder=5, color='#27557b')

#dummy bars for legend
iax2.bar(X_axis+(barwidth*0.55), legend_dummy,edgecolor='black',hatch='//',alpha=alval,label='Baseline', width=barwidth, zorder=5, color='white')
iax2.bar(X_axis-(barwidth*0.55), legend_dummy2,edgecolor='black',alpha=alval,label='CoaXiaL', width=barwidth, zorder=5, color='white')

plt.xticks(X_axis, appNames, fontsize=fs1)

iax2.legend(ncol=2, loc='best',fontsize=fs_legend)

iax2.set_ylabel('Memory Bandwidth\nUsage (GB/s)', fontsize=ylabel_size)

plt.setp(iax2.get_xticklabels(), rotation=45, fontsize=fs_xtick, ha='right')
dx = 0.1; dy = 0 
offset = matplotlib.transforms.ScaledTranslation(dx, dy, ifig.dpi_scale_trans) 
for label in iax2.xaxis.get_majorticklabels():
    label.set_transform(label.get_transform() + offset)



iax2.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, axis='y', alpha=0.4)

plt.yticks(fontsize=fs_ytick)

plt.savefig('mlat_bd_and_mbw_CMP_doublecol.png', bbox_inches='tight')
plt.savefig('mlat_bd_and_mbw_CMP_doublecol.pdf', bbox_inches='tight')




exit
    
