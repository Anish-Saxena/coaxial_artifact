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
import pandas as pd

import argparse

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


legend_labels=['50ns CXL overhead','70ns CXL overhead']

appNames=[]

d50_gains=[]
d70_gains=[]

color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']


appNames = load_object('Workload.pkl')
DDR_ipc = load_object('base.nopam.IPC.pkl')
d50_ipc = load_object('4X.50ns.TH70.IPC.pkl')
d70_ipc = load_object('4X.70ns.TH70.IPC.pkl')


for i in range(len(DDR_ipc)):
    d50ipc_gain = 0
    if(DDR_ipc[i]!=0):
        d50ipc_gain = d50_ipc[i]/DDR_ipc[i]
    d50_gains.append(d50ipc_gain)

for i in range(len(DDR_ipc)):
    d70ipc_gain = 0
    if(DDR_ipc[i]!=0):
        d70ipc_gain = d70_ipc[i]/DDR_ipc[i]
    d70_gains.append(d70ipc_gain)

matplotlib.rcParams.update({'font.size': 20})


#appNames.append('')
#d50_ipc.append(0)
#d70_ipc.append(0)                
#d50_gains.append(0)
#d70_gains.append(0)
#
#appNames.append('GeoMean')
#
#GM_DDR_ipcs= getGeomean(DDR_ipc)
#GM_24_ipcs= getGeomean(d50_ipc)
#GM_50_ipcs= getGeomean(d70_ipc)
#GM_24_gains = getGeomean(d50_gains)
#GM_50_gains = getGeomean(d70_gains)
#
#
#DDR_ipc.append(GM_DDR_ipcs)
#d50_ipc.append(GM_24_ipcs)
#d70_ipc.append(GM_50_ipcs)
#d50_gains.append(GM_24_gains)
#d70_gains.append(GM_50_gains)
#
##print(str(GM_DDR_ipcs))
##print(str(GM_2X_ipcs))
##d50_gains.append(GM_4X_ipcs/GM_DDR_ipcs)
##d70_gains.append(GM_8X_ipcs/GM_DDR_ipcs)
#
#print('gm perfgain all 24ns: '+str(GM_24_ipcs / GM_DDR_ipcs))
#print('gm perfgain all 50ns: '+str(GM_50_ipcs / GM_DDR_ipcs))
#print('gm perfgain all 50ns(correct): '+str(GM_50_gains))



ifig,iax=plt.subplots()
#iax.set_title(field_names[i])
#X_axis = np.arange(pslen*rblen)
X_axis = np.arange(len(appNames))
#print(str(len(appNames)))
#print(str(len(d2X_gains)))
#print(d2X_gains)

barwidth = 0.33
alval=1

###plot all bars normalized to DDR
#ddr_bar = iax.bar(X_axis-(barwidth/2), DDR_arrs[ii],edgecolor='black',alpha=alval, color=color_list[0],label='DDR Memory', width=barwidth, zorder=5)
#d2X_bar = iax.bar(X_axis-(barwidth), d2X_gains,edgecolor='black',alpha=alval, color=color_list[4],label=legend_labels[0], width=barwidth, zorder=5)
d50_bar = iax.bar(X_axis, d50_gains,edgecolor='black',alpha=alval, color=color_list[4],label=legend_labels[0], width=barwidth, zorder=5)
d70_bar = iax.bar(X_axis+(barwidth), d70_gains,edgecolor='black',alpha=alval, color=color_list[6],label= legend_labels[1], width=barwidth, zorder=5)

plt.axhline(y=1, color='black', zorder=5, linestyle=':')
###plotting normalized to 4X
#d2X_bar = iax.bar(X_axis-(barwidth/2), d2X_gains,edgecolor='black',alpha=alval, color=color_list[4],label='2X', width=barwidth, zorder=6)
#d70_bar = iax.bar(X_axis+(barwidth/2), d70_gains,edgecolor='black',alpha=alval, color=color_list[7],label='8X', width=barwidth, zorder=5)


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
appNames[len(appNames)-1]='GM_all'
plt.xticks(X_axis, appNames)
my_yticks=np.arange(0,4,0.5)
plt.yticks(my_yticks)
#iax.set_yticks(np.arange(0, 3, 0.5))
plt.ylim(ymax=3.7)
#iax.legend(ncol=3,bbox_to_anchor=[0.5,1.15], loc='center')
#iax.legend(ncol=3,bbox_to_anchor=[1,0.9], loc='right', fontsize=16)
iax.legend(ncol=1,bbox_to_anchor=[0.88,0.83], loc='right', fontsize=16)
#iax.legend(ncol=1, loc='best', fontsize=16)

#plt.setp(iax.get_xticklabels(), rotation=35, horizontalalignment='center')
plt.setp(iax.get_xticklabels(), rotation=45, ha='right', fontsize=15)
dx =0.1; dy = 0 
offset = matplotlib.transforms.ScaledTranslation(dx, dy, ifig.dpi_scale_trans) 
for label in iax.xaxis.get_majorticklabels():
    label.set_transform(label.get_transform() + offset)

#plt.subplots_adjust(left=0,right=1)
df = pd.DataFrame([1,len(appNames)])
plt.xlim(-1,len(appNames))
#ifig.set_size_inches(10,4)
ifig.set_size_inches(20,3)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int)
plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, axis='y', alpha=0.4)
#plt.ylabel('Performance (IPC) Relative to \nCXL baseline(4X)',fontsize=15)
plt.ylabel('Norm. Performance',fontsize=17, labelpad=10)

iax.tick_params(axis='y', which='major', labelsize=14)
ifig.savefig('70ns_plot.png', bbox_inches='tight')
ifig.savefig('70ns_plot.pdf', bbox_inches='tight')


    

exit
    
