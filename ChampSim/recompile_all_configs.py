import subprocess


#configs=['CONFIGS/12C_2X_CXL_24ns_acho_DRAMSIM.json','CONFIGS/12C_4X_CXL_24ns_1MBLLC_acho_DRAMSIM.json',
#'CONFIGS/12C_4X_CXL_24ns_acho_DRAMSIM.json',
#'CONFIGS/12C_5X_CXL_24ns_acho_DRAMSIM.json',
#'CONFIGS/12C_DDR_acho_DRAMSIM.json',
#'CONFIGS/16C_2X_CXL_24ns_acho_DRAMSIM.json',
#'CONFIGS/16C_4X_CXL_24ns_1MBLLC_acho_DRAMSIM.json',
#'CONFIGS/16C_5X_CXL_24ns_acho_DRAMSIM.json',
#'CONFIGS/16C_DDR_acho_DRAMSIM.json',
#'CONFIGS/8C_2X_CXL_24ns_acho_DRAMSIM.json',
#'CONFIGS/8C_4X_CXL_24ns_1MBLLC_acho_DRAMSIM.json',
#'CONFIGS/8C_4X_CXL_24ns_acho_DRAMSIM.json',
#'CONFIGS/8C_5X_CXL_24ns_acho_DRAMSIM.json',
#'CONFIGS/8C_DDR_acho_DRAMSIM.json',
#'CONFIGS/12C_4X_CXL_50ns_1MBLLC_acho_DRAMSIM.json']

configs=[
 'CONFIGS/12C_DDR_acho_IDEAL_PAM.json','CONFIGS/12C_4X_CXL_50ns_1MBLLC_acho_IDEAL_PAM.json',  
'CONFIGS/12C_4X_CXL_50ns_1MBLLC_acho_PC_CNT.json'     ,'CONFIGS/12C_DDR_acho_PC_CNT.json',
'CONFIGS/12C_4X_CXL_50ns_1MBLLC_acho_TH50.json',       'CONFIGS/12C_DDR_acho_TH50.json',
'CONFIGS/12C_4X_CXL_50ns_1MBLLC_acho_TH60.json',       'CONFIGS/12C_DDR_acho_TH60.json',
'CONFIGS/12C_4X_CXL_50ns_1MBLLC_acho_TH70.json',       'CONFIGS/12C_DDR_acho_TH70.json',
'CONFIGS/12C_4X_CXL_50ns_1MBLLC_acho_NOPAM.json',       'CONFIGS/12C_DDR_acho_NOPAM.json'
]

cmds1=[]
makecmd = 'make -j16'

for cfg in configs:
    cmd1='./config.py '+cfg
    cmds1.append(cmd1)

for cmd1 in cmds1:
    subprocess.run(cmd1, shell=True)
    subprocess.run(makecmd, shell=True)
