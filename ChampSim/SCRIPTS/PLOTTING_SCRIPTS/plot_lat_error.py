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

#def getGeomean(iarr):
#    a=np.array(iarr);
#    return a.prod()**(1.0/len(a))


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


#legend_labels=['Baseline Avg. Latency and Std. Deviation',
#               'CoaXiaL  Avg. Latency and Std. Deviation']
legend_labels=['Baseline','CoaXiaL']

appNames=[]

d24_gains=[]
d50_gains=[]

color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']


appNames = load_object('APPNAME.pkl')
DDR_lat = load_object('DDRLAT.pkl')
CXL_lat = load_object('C4XLAT.pkl')
DDR_std = load_object('DDRSTDEV.pkl')
CXL_std = load_object('C4XSTDEV.pkl')


matplotlib.rcParams.update({'font.size': 24})


ifig,iax=plt.subplots()
X_axis = np.arange(len(appNames))

barwidth = 0.33
alval=1

DDR_bar = iax.bar(X_axis-(barwidth/2), DDR_lat, yerr=DDR_std,edgecolor=color_list[1],alpha=alval, color=color_list[1],label=legend_labels[0], width=barwidth, zorder=5, capsize=5, ecolor=color_list[2])
CXL_bar = iax.bar(X_axis+(barwidth/2), CXL_lat, yerr=CXL_std,edgecolor=color_list[4],alpha=alval, color=color_list[4],label=legend_labels[1], width=barwidth, zorder=0, capsize=5, ecolor=color_list[7])



plt.xticks(X_axis+0.4, appNames)
#my_yticks=np.arange(0,4,0.5)
#plt.yticks(my_yticks)
#iax.set_yticks(np.arange(0, 3, 0.5))
#plt.ylim(ymax=3.0)
plt.ylim(ymin=0.0)
#iax.legend(ncol=3,bbox_to_anchor=[0.5,1.15], loc='center')
iax.legend(ncol=1,bbox_to_anchor=[1,0.85], loc='right', fontsize=28)

#plt.setp(iax.get_xticklabels(), rotation=35, horizontalalignment='center')
plt.setp(iax.get_xticklabels(), rotation=35, ha='right', fontsize=26)
plt.tick_params(axis='x', which='both', length=0)
#dx =0.1; dy = 0 
#offset = matplotlib.transforms.ScaledTranslation(dx, dy, ifig.dpi_scale_trans) 
#for label in iax.xaxis.get_majorticklabels():
#    label.set_transform(label.get_transform() + offset)

#plt.setp(iax.get_xticklabels(), rotation=45, ha='right', fontsize=16)

#plt.subplots_adjust(left=0,right=1)
#df = pd.DataFrame([1,len(appNames)])
plt.xlim(-0.5,len(appNames)-0.5)
#ifig.set_size_inches(10,4)
#ifig.set_size_inches(33,23)
ifig.set_size_inches(6.6, 5.6)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int)
plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, axis='y', alpha=0.4)
#plt.ylabel('Performance (IPC) Relative to \nCXL baseline(4X)',fontsize=15)
plt.ylabel('Average Access Latency \nand Standard Deviation (ns)',fontsize=30, labelpad=10)#,ha='left')
iax.yaxis.set_label_coords(-0.18,0.4)

#iax.tick_params(axis='y', which='major', labelsize=14)
ifig.savefig('lat_stdev_plot.png', bbox_inches='tight')
ifig.savefig('lat_stdev_plot.pdf', bbox_inches='tight')


    

exit
    
