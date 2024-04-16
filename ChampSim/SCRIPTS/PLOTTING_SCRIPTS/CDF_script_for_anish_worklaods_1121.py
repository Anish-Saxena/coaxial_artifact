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

app_list=[
"602.gcc_s-1850B_12T_base.out",
"603.bwaves_s-2931B_12T_base.out",
"605.mcf_s-994B_12T_base.out",
"607.cactuBSSN_s-2421B_12T_base.out",
"619.lbm_s-2677B_12T_base.out",
"620.omnetpp_s-141B_12T_base.out",
"621.wrf_s-6673B_12T_base.out",
"623.xalancbmk_s-10B_12T_base.out",
"627.cam4_s-573B_12T_base.out",
"628.pop2_s-17B_12T_base.out",
"649.fotonik3d_s-10881B_12T_base.out",
"654.roms_s-1007B_12T_base.out",
"ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_26750M.length_250M_12T_base.out",
"ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M_12T_base.out",
"ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_1750M.length_250M_12T_base.out",
"ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_4000M.length_250M_12T_base.out",
"ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_7500M.length_250M_12T_base.out",
"ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_23000M.length_250M_12T_base.out",
"ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
"ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_21500M.length_250M_12T_base.out",
"ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M_12T_base.out",
"ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_184750M.length_250M_12T_base.out",
"ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M_12T_base.out",
"ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_22750M.length_250M_12T_base.out",
"ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
"ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M_12T_base.out",
"ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
"ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_21250M.length_250M_12T_base.out",
"ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_21750M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_51000M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_60750M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_79500M.length_250M_12T_base.out",
"ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_1250M.length_250M_12T_base.out",
"ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_24000M.length_250M_12T_base.out",
"ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_24500M.length_250M_12T_base.out",
"ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_Radii.com-lj.ungraph.gcc_6.3.0_O3.drop_32000M.length_250M_12T_base.out",
"ligra_Radii.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_25000M.length_250M_12T_base.out",
"ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
#"parsec_2.1.canneal.simlarge.prebuilt.drop_1250M.length_250M_12T_base.out",
#"parsec_2.1.facesim.simlarge.prebuilt.drop_1500M.length_250M_12T_base.out",
#"parsec_2.1.fluidanimate.simlarge.prebuilt.drop_9500M.length_250M_12T_base.out",
#"parsec_2.1.raytrace.simlarge.prebuilt.drop_23750M.length_250M_12T_base.out",
#"parsec_2.1.streamcluster.simlarge.prebuilt.drop_14750M.length_250M_12T_base.out"
]


app_list=[
"ligra_Radii.com-lj.ungraph.gcc_6.3.0_O3.drop_32000M.length_250M_12T_base.out",
"ligra_Radii.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_22750M.length_250M_12T_base.out",
"ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
"ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M_12T_base.out",
"ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_21750M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_51000M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_60750M.length_250M_12T_base.out",
"ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_79500M.length_250M_12T_base.out",
"ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_184750M.length_250M_12T_base.out",
"ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M_12T_base.out",
"ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_23000M.length_250M_12T_base.out",
"ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M_12T_base.out",
"ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M_12T_base.out",
"ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_21500M.length_250M_12T_base.out",
"ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M_12T_base.out",
"ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M_12T_base.out",
        ]

### recollect failed ones
app_list=[

"ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_23000M.length_250M_12T_base.out",
"ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M_12T_base.out",


        ]

#app_list = [aname.replace("_12T_base.out",'') for aname in app_list]
#print(app_list)

cur_wd = os.getcwd()
for app in app_list:
    app_dirname=app.replace(".out",'/')
    print(app_dirname)
    #exit(0)
    app_short = app.replace("_12T_base.out",'')
    os.chdir(cur_wd)
    os.mkdir(app_short)
    os.chdir(app_short)
    os.system('scp acho44@keg1.cc.gatech.edu:/shared/acho44/CXL_WD/Anish_pam_configs/4X.50ns.TH70/'+app_dirname+app+' CXL.out')
    os.system('scp acho44@keg1.cc.gatech.edu:/shared/acho44/CXL_WD/Anish_pam_configs/base.nopam/'+app_dirname+app+' DDR.out')
    os.system('python3 ~/CXL_WD/CDF_generate_pickle.py --i DDR.out')
    os.system('python3 ~/CXL_WD/CDF_generate_pickle.py --i CXL.out')
    os.system('python3 ~/CXL_WD/plot_mlatCDF_cmp.py --i '+app_short)
