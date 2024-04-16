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



#parser = argparse.ArgumentParser()
#parser.add_argument('--ylabel', type=str, default='IPC')  
#args = parser.parse_args()
#infile = args.infile

#cxl_delays=['0','30','50','100']


#appNames=[]

fixed_ipcs=[]
d350_ipcs=[]
d450_ipcs=[]
d550_ipcs=[]

#350_pci=[]
#450_pci=[]
#550_pci=[]

d350_norm=[]
d450_norm=[]
d550_norm=[]

appNames = load_object('APPNAME.pkl')

fixed_ipcs=load_object('fixed.pkl')
d350_ipcs=load_object('100_350.pkl')
d450_ipcs=load_object('75_450.pkl') 
d550_ipcs=load_object('50_550.pkl')

d350_norm = [d350_ipcs[i]/fixed_ipcs[i] for i in range(len(fixed_ipcs))]
d450_norm = [d450_ipcs[i]/fixed_ipcs[i] for i in range(len(fixed_ipcs))]
d550_norm = [d550_ipcs[i]/fixed_ipcs[i] for i in range(len(fixed_ipcs))]

#toparr = [[[[[] for m in range(cxlen)] for l in range(mclen)] for k in range(ptlen)] for j in range(rblen)]


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
#color_list= [[['black'] for l in range(ddioslen)] for k in range(ptlen)]
#
#color_list[getindex('2',partitions)][getindex('clean',ddio_setups)]='#A89AE4'
#color_list[getindex('6',partitions)][getindex('clean',ddio_setups)]='#7C67D6'
#color_list[getindex('12',partitions)][getindex('clean',ddio_setups)]= '#42347E'
#
#color_list[getindex('2',partitions)][getindex('nocl',ddio_setups)]='#ABBFB0'
#color_list[getindex('6',partitions)][getindex('nocl',ddio_setups)]='#799A82'
#color_list[getindex('12',partitions)][getindex('nocl',ddio_setups)]='#3D5A45'
#color_list[getindex('ideal',partitions)][getindex('clean',ddio_setups)] ='#C26989'
color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']




GM_fixed_ipcs= getGeomean(fixed_ipcs)
GM_350_ipcs= getGeomean(d350_ipcs)
GM_450_ipcs= getGeomean(d450_ipcs)
GM_550_ipcs= getGeomean(d550_ipcs)


fixed_ipcs.append(GM_fixed_ipcs)
d350_ipcs.append(GM_350_ipcs)
d450_ipcs.append(GM_450_ipcs)
d550_ipcs.append(GM_550_ipcs)

###CPI
#d350_norm.append( GM_fixed_ipcs / GM_350_ipcs)
#d450_norm.append( GM_fixed_ipcs / GM_450_ipcs)
#d550_norm.append( GM_fixed_ipcs / GM_550_ipcs)

#appNames.append('')
#d350_norm.append(0) 
#d450_norm.append(0)
#d550_norm.append(0)    

appNames.append('gm')
##IPC
d350_norm.append( GM_350_ipcs / GM_fixed_ipcs  )
d450_norm.append( GM_450_ipcs / GM_fixed_ipcs  )
d550_norm.append( GM_550_ipcs / GM_fixed_ipcs  )



ifig,iax=plt.subplots()
#iax.set_title(field_names[i])
#X_axis = np.arange(pslen*rblen)
X_axis = np.arange(len(appNames))

barwidth = 0.2
alval=1

d350_bar = iax.bar(X_axis-(barwidth), d350_norm,edgecolor='black',alpha=alval, color=color_list[4],label='(100ns,350ns)', width=barwidth, zorder=6)
d450_bar = iax.bar(X_axis, d450_norm,edgecolor='black',alpha=alval, color=color_list[5],label='(75ns,450ns)', width=barwidth, zorder=6)
d550_bar = iax.bar(X_axis+(barwidth), d550_norm,edgecolor='black',alpha=alval, color=color_list[7],label='(50ns,550ns)', width=barwidth, zorder=6)
#d350_bar = iax.bar(X_axis-(barwidth), d350_norm,edgecolor='black',alpha=alval, color=color_list[4],label='80% 100ns, 20% 350ns', width=barwidth, zorder=6)
#d450_bar = iax.bar(X_axis, d450_norm,edgecolor='black',alpha=alval, color=color_list[5],label='80% 75ns,   20% 450ns', width=barwidth, zorder=6)
#d550_bar = iax.bar(X_axis+(barwidth), d550_norm,edgecolor='black',alpha=alval, color=color_list[7],label='80% 50ns,   20% 550ns', width=barwidth, zorder=6)

iax.axhline(y=1,color='black',linestyle='--')

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

plt.xticks(X_axis, appNames, fontsize=24)
#iax.legend(ncol=3,bbox_to_anchor=[0.44,1.15], loc='center', fontsize=19)
iax.legend(ncol=1,bbox_to_anchor=[1.23,0.5], loc='center', fontsize=22)

plt.setp(iax.get_xticklabels(), rotation=15, horizontalalignment='center')
ifig.set_size_inches(10,3)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, axis='y', alpha=0.3) #for pdf
plt.grid(color='gray', linestyle='--', linewidth=0.7, markevery=int, zorder=1, axis='y', alpha=0.9) #for png
plt.grid(color='gray', linestyle='--', linewidth=0.7, which='minor', zorder=1, axis='y', alpha=0.9) #for png
plt.ylabel('Performance norm.\nto Fixed Latency',fontsize=24, labelpad=10)
iax.yaxis.set_label_coords(-0.1,0.4)
#iax.set_yticklabels(iax.get_yticks(), fontsize=20)
plt.tick_params(axis='y', which='major', labelsize=22)
iax.set_yticks([i/4 for i in range(4)], minor=True, len=10)

ifig.savefig('memvar_exp_plot_ipc.png', bbox_inches='tight')
ifig.savefig('memvar_exp_plot_ipc.pdf', bbox_inches='tight')

print(d350_norm) 
print(d450_norm) 
print(d550_norm) 

exit
    
