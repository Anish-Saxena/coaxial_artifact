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
parser.add_argument('--i', type=str, default='res.txt')                         
args=parser.parse_args()
#from scipy.stats import norm

#resfile = 'raytrace_DDR.out'
#resfile = 'streamcluster_CXL.out'
resfile=args.i

#with open(resfile, 'r') as rf:

rf = open(resfile, 'r')
line=rf.readline()
while('LAT_HIST' not in line):
    line=rf.readline()

line=rf.readline()
line=rf.readline()
line=rf.readline()
if('this stat is' in line):
    line=rf.readline()


#line=rf.readline()
#line=rf.readline()

memlathist=[0]*200;

for i in range(0,200):
    tmp=line.split(":")
    #print(str(i))
    #print(tmp[0])
    assert(i*10==(int(tmp[0])))
    memlathist[i]+=int(tmp[1])
    line=rf.readline()

memlathist[0]=0

allacc = sum(memlathist)
#mlat_pdf = memlathist / sum(memlathist)
mlat_pdf = [x / allacc for x in memlathist]
mlat_cdf = np.cumsum(mlat_pdf)

p99=0
p95=0
p90=0
p80=0
p70=0
median=0

for a in range(200):
    cd=mlat_cdf[a]
    if(cd>=0.99):
        if(p99==0):
            p99=a*10;
    if(cd>=0.95):
        if(p95==0):
            p95=a*10;
    if(cd>=0.90):
        if(p90==0):
            p90=a*10;
    if(cd>=0.80):
        if(p80==0):
            p80=a*10;
    if(cd>=0.70):
        if(p70==0):
            p70=a*10;
    if(cd>=0.50):
        if(median==0):
            median=a*10;


print(resfile)
m_sum=0
for i in range(200):
    #a=mlat_pdf[i]*(i*5)
    #m_sum=m_sum+a
    a=memlathist[i]*(i*10)
    m_sum=m_sum+a
print('mean: '+str(m_sum/allacc))
m_sum=m_sum/allacc

a_sum=0
#for i in range(300):
#    #a=mlat_pdf_DDR[i]*(((i*5)-(all_lat_avg/2)) * ((i*5)-(all_lat_avg/2)) )
#    a=mlat_pdf[i]*(((i*5)-m_sum) * ((i*5)-(m_sum)) )
#    a_sum=a_sum+a
#stdev=math.sqrt(a_sum)
#print('stdev: '+str(stdev)) 

biglist = []
for i in range(200):
    for j in range(memlathist[i]):
        biglist.append(i*10)

mean=np.mean(biglist)
stdev=np.std(biglist)
print('mean: '+str(mean)) 
print('stdev: '+str(stdev)) 

mean_stdev=[]
mean_stdev.append(mean)
mean_stdev.append(stdev)

#pklfname = resfile.replace('.out','_cdf.pkl')
pklfname = 'DDR_cdf.pkl'
if('CXL' in resfile):
    pklfname = 'CXL_cdf.pkl'
with open(pklfname, 'wb') as pickle_file:
    pickle.dump(mlat_cdf, pickle_file)

spklfname = 'DDR_mean_var.pkl'
if('CXL' in resfile):
    spklfname = 'CXL_mean_var.pkl'
with open(spklfname, 'wb') as pickle_file2:
    pickle.dump(mean_stdev, pickle_file2)


