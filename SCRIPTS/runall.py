import os
import subprocess

def run_champsim(path_to_traces, champsim_run='champsim_run.py'):
    # List all files in the directory
    trace_files = [f for f in os.listdir(path_to_traces) if f.endswith('.xz')]

    for trace_file in trace_files:
        full_trace_path = os.path.join(path_to_traces, trace_file)
        trace_name = os.path.splitext(trace_file)[0]  # Get the trace file name without extension

        # First command
        cmd1 = [
            'python3', champsim_run, 
            '--cfg', '12C_4X_CXL_50ns_1MBLLC_TH70', 
            '--tr', full_trace_path, 
            '--out_dir', f'CXL_{trace_name}'
        ]
        
        # Second command
        cmd2 = [
            'python3', champsim_run, 
            '--cfg', '12C_base_DDR_NOPAM', 
            '--tr', full_trace_path, 
            '--out_dir', f'Baseline_{trace_name}'
        ]

        # Run the commands
        subprocess.run(cmd1)
        subprocess.run(cmd2)

# Example usage
path_to_traces = '/nethome/SCAE/coaxial_AE/TRACES/STREAM_TRACES/' ##SCAE replace to your trace path
csrunscript = 'champsim_run.py'
run_champsim(path_to_traces, csrunscript)

