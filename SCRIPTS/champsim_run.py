
import os
import sys
import argparse
import random

# parse cmd args
parser = argparse.ArgumentParser()
#SCAE# Change PATH to your Champsim
parser.add_argument('--champsim_dir', type=str,
                    default='/nethome/SCAE/coaxial_AE/ChampSim/')
parser.add_argument('--out_dir', type=str, default='out_dir')
parser.add_argument('--cfg', type=str, default='DDR')
parser.add_argument('--tr', type=str, default='SCAEXXX') #trace
parser.add_argument('--wi', type=str, default='1000000') #warmup insts
parser.add_argument('--si', type=str, default='200000000') #sim insts
parser.add_argument('--printstd', type=str, default='0')

#parser.add_argument('--num_server', type=str, default='8')
#parser.add_argument('--num_proc', type=str, default='0')
#parser.add_argument('--llc_size', type=str, default='0')
#parser.add_argument('--mem_controllers', type=str, default='1')
#parser.add_argument('--cxl_delay', type=str, default='0')
#parser.add_argument('--wsize', type=str, default='0')
args = parser.parse_args()

# 1st input: the output directory you want the run to take place + store results
#outdir = sys.argv[1]
outdir = args.out_dir
if (os.path.isdir(outdir)):
    print('directory already exists! aborting')
    exit(0)
#os.system('rm -rf '+outdir)
os.system('mkdir '+outdir)
os.chdir(outdir)

champsim_dir = args.champsim_dir
cfg = args.cfg
tr  = args.tr
wi  = args.wi
si  = args.si

printstd = args.printstd

#SCAE populate PATHS#
tr_stream_triad="XXXX/streamtraid.trace.xz"
tr_stream_add="/XXXX/"

cmd = champsim_dir+'bin/'+cfg+' --warmup_instructions '+wi+' --simulation_instructions '+si+' '+tr
print(cmd)
#exit(0)

# launch the run, redirectung stdin and stderr to log files

##os.system('./zsim conf.cfg 1> res.txt 2>app.txt &')
if '1' in printstd:
    #print('warning - not redirecting output, stats will not be saved!')
    #os.system('timeout 30m ./zsim conf.cfg')
    os.system(cmd + '|tee res.txt')
else:
    os.system(cmd+' 1> res.txt 2>app.txt &')
    #os.system(cmd+' &> res.txt &')
    #os.system(
    #    '{(./zsim conf.cfg 1> res.txt 2>app.txt) ; (python /shared/srikar/cxl_dev/notify.py);} &')
#os.system('python3 ../process_timestamps.py')
os.system('cd ..')
