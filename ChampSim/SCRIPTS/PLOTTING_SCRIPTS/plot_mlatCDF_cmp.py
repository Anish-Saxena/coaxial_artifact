#!/usr/bin/env python3

import os
import sys 
import csv 
import math
import statistics
import numpy as np
from os.path import exists
import matplotlib
import matplotlib.pyplot as plt 
import argparse
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

import pickle
parser = argparse.ArgumentParser()                                              
parser.add_argument('--i', type=str, default='streamcluster') #appname
args=parser.parse_args()



def load_object(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception as ex:
        print("Error during unpickling object (Possibly unsupported):", ex)


mlat_cdf_DDR = load_object('DDR_cdf.pkl')
mlat_cdf_CXL = load_object('CXL_cdf.pkl')
DDR_mstv = load_object('DDR_mean_var.pkl')
CXL_mstv = load_object('CXL_mean_var.pkl')

DDR_mstv=[round(x) for x in DDR_mstv]
CXL_mstv=[round(x) for x in CXL_mstv]

DDR_amat = DDR_mstv[0]
CXL_amat = CXL_mstv[0]

DDR_var = DDR_mstv[1]
CXL_var = CXL_mstv[1]

appname=args.i

color_list=[ '#ABBFB0', '#799A82', '#3D5A45','darkslategrey', '#A89AE4', '#7C67D6', 'darkslateblue','#42347E']
####### Plotting CDF
#cdf_x_axis=[10*x for x in range(100)]
matplotlib.rcParams.update({'font.size': 60})
cdf_x_axis=[5*x for x in range(200)] #10*x in cycles, but / 2 to convert ot NS
ifig,iax=plt.subplots()
linewidth=15
plt.plot(cdf_x_axis,mlat_cdf_DDR, label="Baseline", linewidth=linewidth, color=color_list[2], linestyle='--')
plt.plot(cdf_x_axis,mlat_cdf_CXL, label="CoaXiaL", linewidth=linewidth , color=color_list[5])

plt.axvline(x = DDR_amat, color = color_list[2], linewidth=linewidth, linestyle='--')
plt.axvline(x = CXL_amat, color = color_list[5], linewidth=linewidth)

fs_legend=140
fs1=175

iax.set_xlim(xmin=0)
iax.set_ylim(ymin=0)
iax.set_xlim(xmax=300)
iax.legend(ncol=1,fontsize=fs_legend)
plt.ylabel('CDF',fontsize=fs1, labelpad=45)
plt.xlabel('Memory Access Time (ns)',fontsize=fs1, labelpad=45)
iax.yaxis.set_label_coords(-0.17, 0.65)
iax.xaxis.set_label_coords(0.425, -0.17)
plt.grid(color='gray', linestyle='--', linewidth=0.2, zorder=0, alpha=0.3)
plt.grid(color='gray', linestyle='--', linewidth=0.2, zorder=0, alpha=0.3,which='minor')
#iax.tick_params(axis='both', which='major', labelsize=120)
#props = dict(boxstyle='round', facecolor='white', alpha=0.7)
#props = dict(boxstyle='square,pad=0.1',facecolor='white', alpha=0.7)
props = dict(facecolor='white', alpha=0.8)
#iax.text(-145,1.1,btext,zorder=5, fontsize=fs1, ha='left',bbox=props);
#iax.text(300,1.1,btext,zorder=5, fontsize=fs1, ha='center',bbox=props);
#%raw data: DDR avg, DDR stdev, CXL avg, CXL stdev
#% perlbench: 55.4	49.9	81.7	46.9
#% Moses: 262.5	222.0	124.0	99.9
#plt.setp(iax.get_yticklabels()[0], visible=False)
#plt.setp(iax.get_yticklabels()[-1], visible=True)


rows=['Baseline','CoaXiaL']
columns=['mean','stdev']
cell_text = [[DDR_amat,DDR_var],[CXL_amat,CXL_var]]
tab = plt.table(cellText=cell_text,
                      rowLabels=rows,
                      #rowColours=colors,
                      colLabels=columns,
                      bbox=[0.3,1.045,0.7,0.5],
                      cellLoc='center', alpha=1)
                      #loc='top')#, linewidth=2)
tab.auto_set_font_size(False)
tab.set_fontsize(fs1)
#tab.Cell.set_linewidth(10)
for key, cell in tab.get_celld().items():
    cell.set_linewidth(5)

major_ticks = np.arange(0, 1.1, 0.2)
iax.set_yticks(major_ticks)
x_minor_ticks=(0,600,100)
iax.tick_params(axis='x', which='minor', bottom=False)
ml = MultipleLocator(100)
iax.xaxis.set_minor_locator(ml)
#iax.xaxis.set_minor_locator(AutoMinorLocator())
#iax.tick_params(axis='both', which='minor')

labels = iax.yaxis.get_major_ticks()
labels[0].set_visible(False)
#xxlabels = iax.xaxis.get_major_ticks()
#xxlabels[-1].set_visible(False)


#labels[0]=lables[-1]=""
#iax.set_yticklabels(labels)
iax.tick_params(axis='both', which='major', labelsize=140, length=30, width=3)
ifig.set_size_inches(33,23)
#plt.subplots_adjust(top=1.1)
ifig.savefig('mem_lat_cdf_cut300_'+appname+'.png', bbox_inches='tight')
ifig.savefig('mem_lat_cdf_cut300_'+appname+'.pdf', bbox_inches='tight')
ifig.tight_layout(pad=0)
#ifig.tight_layout(pad=2)
#ifig.savefig('mem_lat_cdf_cut600.png')

