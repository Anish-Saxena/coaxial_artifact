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


parser = argparse.ArgumentParser()
parser.add_argument('--infile', type=str, default='bwlat.csv')  
parser.add_argument('--outdir', type=str, default='BW_LAT_lineplot')
parser.add_argument('--plotAll', type=bool, default=False)
args = parser.parse_args()
infile = args.infile
outdir = args.outdir
plotAll = args.plotAll

print(infile)

freq_in_GHz = 2.4
num_ddr_cont=1
mbw_ddr_cap = 38.4 * num_ddr_cont
#mbw_ddr_cap = 23.84 * num_ddr_cont


#toparr = [[] for i in range(mclen)]

MBWS = []
MBW_UTILS = []
AVGLATS = []
LAT90S = []
#IPCS = []


def getindex(elem, arr):
    for i in range(len(arr)):
        if str(arr[i])==elem:
            return i
    print('didnt find elem '+elem+' in arr')
    exit
    return -1

def get_ds_index(elem):
    if 'clean' in elem:
        if ('clean' in ddio_setups):
            return 1
        else:
            return -1
    else:
        return 0



field_names=[]
field_names.append('MBW')
field_names.append('MBW_UTIL')
field_names.append('AVGLAT')
field_names.append('LAT90')
field_names.append('IPC')
#field_names.append('MPKI')
#field_names.append('L3_MR')
#field_names.append('wr_lat_avg')
#field_names.append('rd_lat_avg')
#field_names.append('all_lat_avg')
#field_names.append('svc_time_avg')
#color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']
#color_list=[ '#3D5A45','darkslategrey', '#7C67D6', 'darkslateblue','#42347E']
color_list=[ '#3D5A45','darkslategrey', '#A89AE4', '#42347E', 'darkslateblue']
#colors = [ '#ABBFB0', '#799A82', '#3D5A45',       '#C26989', '#6e92f2']
# greens: '#a4c1ab','#3b6d56',                                                  
#purples warm: '#dba5ce','#7B476F','#451539',                                   
# oranges: '#FFC966','#e58606','#ffa500'                                        
# reds: '#4B0215',                                                              
# blues:'#6e92f2',  

#purples:  '#A89AE4', '#7C67D6', '#42347E',

if infile in os.listdir('.'):
    f=open(infile,'r')
    line=f.readline();
    line=f.readline();
    expected_cores=1;
    while line:
        tmp=line.split(',')
        #### parse setup
        #assert(expected_cores==int(tmp[0]))
        #if ((int(expected_cores) % 2) != 0):
        #    expected_cores=expected_cores+1
        #    line=f.readline();
        #    continue

        expected_cores=expected_cores+1
 
        bw_multiplier = 1;
        mbw_cap = 38.4 * num_ddr_cont* bw_multiplier

        avgLat_in_ns = float(tmp[2])/freq_in_GHz
        Lat90_in_ns = float(tmp[3])/freq_in_GHz
        
        ## modeled DDR5 to be split into 2 logical channels. Multiply BW by 2X
        #mbw_raw=2*(float(tmp[1]))
        mbw_raw=(float(tmp[1]))
        MBWS.append(mbw_raw);
        MBW_UTILS.append(((mbw_raw) / mbw_cap)*100);
        AVGLATS.append(avgLat_in_ns);
        LAT90S.append(Lat90_in_ns);
        #IPCS.append(float(tmp[4]));
        
       #print(str(mci)+str(qdi)+str(dsi))

        line=f.readline();

    print('toparr populated')
    
    os.system('mkdir '+outdir)
    os.chdir(outdir)

    matplotlib.rcParams.update({'font.size': 40})

    xtick_labels=[]
    for k in range(1,len(MBWS)+1):
        if(k%2==0):
            xtick_labels.append(str(k))
        else:
            xtick_labels.append('')

    
    #put arrays in a top array, for easier loop coding
    toparr=[]
    toparr.append(MBWS)
    toparr.append(MBW_UTILS)
    toparr.append(AVGLATS)
    toparr.append(LAT90S)
    #toparr.append(IPCS)
    #field_names = ['MBW','LAT','IPC']

        
    ifig,iax=plt.subplots()
    #iax.set_title(field_names[i])
    #X_axis = np.arange())

    barwidth = 15
    ### just plot one ideal mc

    alval=1

    #iax.plot(MBWS, AVGLATS, label='Average Latency', alpha=alval, color=color_list[2], linewidth=barwidth, zorder=5)
    #iax.plot(MBWS, LAT90S, label='90% Latency', alpha=alval, color=color_list[3], linewidth=barwidth, zorder=4)
    
    iax.plot(MBW_UTILS, AVGLATS, label='Average Latency', alpha=alval, color=color_list[2], linewidth=barwidth, zorder=5)
    iax.plot(MBW_UTILS, LAT90S, label='90% Latency', alpha=alval, color=color_list[3], linewidth=barwidth, zorder=4)
    plt.axvline(x=60, linewidth=barwidth/3, color='black', linestyle='--')
    plt.axhline(y=160, linewidth=barwidth/3, color='black', linestyle='--')
    plt.axhline(y=285, linewidth=barwidth/3, color='black', linestyle='--')
    
    #plt.axvline(x=60, linewidth=barwidth/3, color='green', linestyle='--')
    #plt.axvline(x=15, linewidth=barwidth/3, color='green', linestyle='--')
    #plt.axvline(x=80, linewidth=barwidth/3, color='orange', linestyle='--')
    #plt.axvline(x=20, linewidth=barwidth/3, color='orange', linestyle='--')
   
    myfontsize=50
    
    #iax.legend(bbox_to_anchor=(0.5,1.2) , ncol=1, loc='upper left')#, columnspacing=)
    iax.legend(ncol=1, loc='upper left',fontsize=myfontsize)#, columnspacing=)

    #plt.xticks(X_axis, xtick_labels, horizontalalignment='center')
    #iax.legend(bbox_to_anchor=(0.5,1.2) , ncol=1, loc='center')#, columnspacing=)
    plt.setp(iax.get_xticklabels(), horizontalalignment='center')
    #ifig.set_size_inches(16,3)
    ifig.set_size_inches(20,15)
    #plt.subplots_adjust(bottom=0.2)
    plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=0, axis='both', alpha=0.5)
    #plt.grid(color='black', linestyle='--', linewidth=0.4, markevery=int, zorder=0, axis='both', alpha=0.9)

    #plt.xlabel('\nType_Delay(ns)')
    iax.set_ylim([0,510])
    iax.set_xlim([0,69])
    plt.ylabel('Memory Access Latency (ns) \n', fontsize=myfontsize)
    #plt.xlabel('\nMemory Bandwidth (GB/s)')
    plt.xlabel('\nMemory Bandwidth Utilization as \n% of Theoretical Peak',fontsize=myfontsize)



    ifig.savefig('BW_LATENCY_motivation_util.png', bbox_inches='tight')
    ifig.savefig('BW_LATENCY_motivation_util_champsim.pdf', bbox_inches='tight')
    #ifig.savefig(field_names[i]+'.png',dpi=1000)
        


exit
    
