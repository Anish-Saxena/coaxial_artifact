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



#server_apps=['moses','imgdnn','xapian','sphinx','masstree','mica','bc','pr','bfs','tc','sssp','cc','monetDB']
cxl_delay = 25

#appNames=[]

ipc_gains=[]
sa_ipc_gains=[]
sp_ipc_gains=[]
#fields = ['IPC', 'Memory BW Utilization', 'Average Memory Latency']


#DDR_mbws=[]
#DDR_mlats=[]
#lowload_mlats=[]
dummy_for_MBW_label=[]

#CXL_mbws=[]
#CXL_mlats=[]
#toparr = [[[[[] for m in range(cxlen)] for l in range(mclen)] for k in range(ptlen)] for j in range(rblen)]

ddr5_BW = 38.4

#appNames = load_object('APPNAME.pkl')
#DDR_mbws = load_object('DDRBW.pkl')
#DDR_mlats= load_object('DDRLAT.pkl')
#CXL_mbws = load_object('C4XBW.pkl')
#CXL_mlats= load_object('C4XLAT.pkl')
#DDR_ipc = load_object('DDRIPC.pkl')
#CXL_ipc = load_object('C4XIPC.pkl')

appNames = load_object('Workload.pkl')
DDR_mbws = load_object('base.nopam.BW.pkl')
#DDR_mlats= load_object('DDR_L2LAT.pkl')
DDR_mlats= load_object('DDR_LLCLAT.pkl')
CXL_mbws = load_object('4X.50ns.TH70.BW.pkl')
#CXL_mlats= load_object('CXL_L2LAT.pkl')
CXL_mlats= load_object('CXL_LLCLAT.pkl')
DDR_ipc = load_object('base.nopam.IPC.pkl')
CXL_ipc = load_object('4X.50ns.TH70.IPC.pkl')
ipc_gains = load_object('speedup.pkl')

#DDR_pam_ratios = load_object('DDR_PAM_RATIO.pkl')
CXL_pam_ratios = load_object('CXL_PAM_RATIO.pkl')



appNames_updated = [name.replace("GM", "Mean") if "GM" in name else name for name in appNames]
appNames_updated[len(appNames_updated)-1]="Mean_all"
print(appNames_updated[len(appNames_updated)-1])
appNames= appNames_updated
appNames_ipc=appNames
#len_without_means=len(appNames)-6
#appNames=appNames[:len_without_means]
#DDR_mbws=DDR_mbws[:len_without_means]
#DDR_mlats=DDR_mlats[:len_without_means]
#CXL_mbws=CXL_mbws[:len_without_means]
#CXL_mlats=CXL_mlats[:len_without_means]

DDR_mlats=[x/2.4 for x in DDR_mlats]
CXL_mlats=[x/2.4 for x in CXL_mlats]

print(DDR_mlats)

print(appNames)
num_apps = len(appNames)

DDR_onchip_delay = [26] * num_apps # PAM is off for baseline, so ratio is 0
CXL_onchip_delay = [0] * num_apps

lowload_mlats = [50.0] * num_apps
for i in range(len(DDR_mlats)):
    if(DDR_mlats[i]==0):
        lowload_mlats[i]=0;
        DDR_onchip_delay[i]=0
    else:
        # derive on chip latency
        cxl_pam_ratio = CXL_pam_ratios[i]
        if(cxl_pam_ratio>0):
            cxl_pam_ratio = 100
        #on_chip_delay = (cxl_pam_ratio * 9 + ((100-cxl_pam_ratio)*26)) / 100
        on_chip_delay = (cxl_pam_ratio * 9 + ((100-cxl_pam_ratio)*26)) / 100
        CXL_onchip_delay[i] = on_chip_delay


#color_list[getindex('ideal',partitions)][getindex('clean',ddio_setups)] ='#C26989'
color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']


################# PLOT latency breakdown ##################3

cxl_50nsdel=[]
for i in range(len(lowload_mlats)):
    if(lowload_mlats[i]!=0):
        cxl_50nsdel.append(50)
    else:
        cxl_50nsdel.append(0)

### overlapping mlat with low lowad lat makes the plot fat...
DDR_QD =[]
DDR_QD_bottom =[]
for i in range(len(DDR_mlats)):
    if(DDR_mlats[i]==0):
        DDR_QD.append(0)
        DDR_QD_bottom.append(0)
    else:
        DDR_QD.append(DDR_mlats[i]+17 - lowload_mlats[i] - DDR_onchip_delay[i])
        DDR_QD_bottom.append(lowload_mlats[i]+DDR_onchip_delay[i])
CXL_QD =[]
CXL_QD_bottom=[]
CXL_50nsdel_bottom=[]
for i in range(len(CXL_mlats)):
    if(lowload_mlats[i]!=0):
        CXL_QD.append((CXL_mlats[i]+17 - lowload_mlats[i])-cxl_50nsdel[i] - CXL_onchip_delay[i])
        CXL_QD_bottom.append(lowload_mlats[i]+cxl_50nsdel[i]+CXL_onchip_delay[i])
        CXL_50nsdel_bottom.append(lowload_mlats[i]+ CXL_onchip_delay[i])
    else:
        CXL_QD.append(0)
        CXL_QD_bottom.append(0)
        CXL_50nsdel_bottom.append(0)

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

#plt.text(len(ipc_gains)-0.5,100,'geoMean',fontsize=fs_xtick,rotation=0, va='top')
#iax0.text(len(ipc_gains)-1, -0.2, 'GeoMean', fontsize=fs_xtick,rotation=90, ha='center', va='top')
mean_range_begin = len(appNames_ipc) - 5
mean_range_end = len(appNames_ipc)
for i in range(mean_range_begin, mean_range_end):
    #iax0.text(i, -0.2, appNames_ipc[i], fontsize=fs_xtick,rotation=270, ha='center', va='top')
    if(ipc_gains[i]<3.5):
        iax0.text(i,ipc_gains[i]+0.15,str(round(ipc_gains[i],2)),zorder=5, fontsize=fs_smalltext, ha='center', rotation=45);
    else:
        iax0.text(i,2.5+0.15,str(round(ipc_gains[i],2)),zorder=5, fontsize=fs_smalltext, ha='center', rotation=45);



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
#iax0.text(28,1.9,'geoemans',zorder=5, fontsize=12, ha='left', bbox=props);
#iax0.text(28,0.9,'server',zorder=5, fontsize=12, ha='left', bbox=props);

iax0.set_xticks([], [])
iax0.set_ylabel('Normalized\nPerformance', fontsize=ylabel_size)
iax0.tick_params(axis='y', which='major', labelsize=fs_ytick)
major_ticks = np.arange(0, 3.3, 0.5)
iax0.set_yticks(major_ticks)
iax0.grid(color='gray', linestyle='--', linewidth=0.2, markevery=float, zorder=1, alpha=0.4)


##### plot mlat breakdown for qd and st

X_axis = np.arange(len(appNames))
print(str(len(X_axis)))
print(str(len(lowload_mlats)))

onchip_color = '#FFA500'

barwidth = 0.3
alval=1
iax1.bar(X_axis-(barwidth*0.55), lowload_mlats,edgecolor='black',hatch='//',alpha=alval, color='indigo', width=barwidth, zorder=5)
iax1.bar(X_axis-(barwidth*0.55), DDR_QD,edgecolor='black',alpha=alval, hatch='//', color='lavender', width=barwidth, zorder=4, bottom=DDR_QD_bottom)
iax1.bar(X_axis-(barwidth*0.55), DDR_onchip_delay,edgecolor='black',alpha=alval, hatch='//', color=onchip_color, width=barwidth, zorder=4, bottom=lowload_mlats)


iax1.bar(X_axis+(barwidth*0.55), CXL_QD,edgecolor='black',alpha=alval, color='lavender', width=barwidth, zorder=4,label='Queuing Delay' , bottom=CXL_QD_bottom)
iax1.bar(X_axis+(barwidth*0.55), lowload_mlats,edgecolor='black',alpha=alval, color='indigo', width=barwidth, zorder=5, label='Access Service Time',) #redundant, no label, use same color
iax1.bar(X_axis+(barwidth*0.55), cxl_50nsdel,edgecolor='black',alpha=alval, color='#bf77be',label='CXL Interface Delay', width=barwidth, zorder=4, bottom=CXL_50nsdel_bottom)
iax1.bar(X_axis+(barwidth*0.55), CXL_onchip_delay,edgecolor='black',alpha=alval, color=onchip_color,label='On-chip Time', width=barwidth, zorder=4, bottom=lowload_mlats)



iax1.tick_params(axis='y', which='major', labelsize=fs_ytick)
#plt.xticks(X_axis, appNames, fontsize=10)
#iax1.legend(ncol=3,bbox_to_anchor=[0.5,1.3], loc='center', fontsize=16)
#iax1.legend(ncol=1,bbox_to_anchor=[1,0.9], loc='right', fontsize=16)
#iax1.legend(ncol=3,loc='best')
iax1.legend(ncol=4,loc='best',fontsize=fs_legend)
iax1.set_xticks([], [])
iax1.set_ylabel('Average L2C Miss\n Latency (ns)', fontsize=ylabel_size)
iax1.set_ylim(0,530)
#iax1.text(20,100,'To update with data',zorder=5, fontsize=15)
#iax1.text(0,181,'356ns',zorder=5, fontsize=fs_smalltext)
#empty text to create whitespace
#iax1.text(30,0,' ',zorder=5, fontsize=12)
major_ticks2 = np.arange(0, 550, 100)
iax1.set_yticks(major_ticks2)
plt.yticks(fontsize=fs_ytick)
#plt.setp(iax1.get_xticklabels(), rotation=45, ha='right', fontsize=13)
#plt.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1)
iax1.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, alpha=0.4)

#ifig.savefig('mlat_qd_st_DDR.png', bbox_inches='tight')



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
#iax.legend(ncol=2, reversed(handles), reversed(labels), loc='upper left')
#iax2.legend(ncol=1,loc='best',fontsize=fs_legend)
#iax2.legend(ncol=1,bbox_to_anchor=(1,0.4), loc='center',fontsize=fs_legend)
#iax2.legend(ncol=1, loc='upper right',fontsize=fs_legend)
iax2.legend(ncol=2, loc='best',fontsize=fs_legend)
#iax3=iax2.twinx()
#iax3.set_ylabel('Memory Bandwidth\nUtilization')
iax2.set_ylabel('Memory Bandwidth\nUsage (GB/s)', fontsize=ylabel_size)
#iax.set_ylabel('Memory Bandwidth Utilization')
#iax.set_ylim(0,200)
#iax.text(-0.5,201,'356ns',zorder=5, fontsize=10)

#plt.setp(iax.get_xticklabels(), rotation=35, horizontalalignment='center')
#plt.setp(iax2.get_xticklabels(), rotation=45, ha='right', fontsize=fs_xtick)
plt.setp(iax2.get_xticklabels(), rotation=45, fontsize=fs_xtick, ha='right')
dx = 0.1; dy = 0 
offset = matplotlib.transforms.ScaledTranslation(dx, dy, ifig.dpi_scale_trans) 
for label in iax2.xaxis.get_majorticklabels():
    label.set_transform(label.get_transform() + offset)

#iax2.text(26,-0.6,'(geomeans only for performance)',zorder=5, fontsize=12)

iax2.grid(color='gray', linestyle='--', linewidth=0.2, markevery=int, zorder=1, axis='y', alpha=0.4)
#ifig.set_size_inches(20,10)
#plt.set_size_inches(20,10)
#plt.ylabel(fields[ii])

plt.yticks(fontsize=fs_ytick)

#ifig.savefig('all_apps_mbw_DDR.png', bbox_inches='tight')
#ifig.savefig('mlat_bd_and_mbw_CMP.png', bbox_inches='tight')
plt.savefig('mlat_bd_and_mbw_CMP_doublecol.png', bbox_inches='tight')
plt.savefig('mlat_bd_and_mbw_CMP_doublecol.pdf', bbox_inches='tight')




exit
    
