import re
import os

i_base_nopam = 0
i_base_pc_cnt = 1
i_base_th50 = 2
i_base_th60 = 3
i_base_th70 = 4
i_base_ideal=5
i_cxl_nopam = 6
i_cxl_pc_cnt = 7
i_cxl_th50 = 8
i_cxl_th60 = 9
i_cxl_th70 = 10
i_cxl_ideal=11

num_cfgs = 12

ii_ipcs = 0
ii_llc_misslat = 1
ii_l2_misslat = 2
ii_ALL_PAM = 3
ii_False_Positive = 4
ii_False_Negative = 5
ii_LLC_Misses = 6

sum_all_pam = [0] * num_cfgs
sum_false_positive = [0] * num_cfgs
sum_false_negative = [0] * num_cfgs

def get_custom_index(subdir):
    # Convert subdir to lower case for case-insensitive comparison
    subdir_lower = subdir.lower()

    #ignore unrelated configs
    if '1212' not in subdir_lower:
        return -1
    if '2x' in subdir_lower:
        return -1
    if '8x' in subdir_lower:
        return -1
    if '70ns' in subdir_lower:
        return -1
    if '10ns' in subdir_lower:
        return -1

    # Check the name of the subdir and assign the index accordingly
    if 'base' in subdir_lower and 'nopam' in subdir_lower:
        return i_base_nopam
    elif 'base' in subdir_lower and 'pc_cnt' in subdir_lower:
        return i_base_pc_cnt
    elif 'base' in subdir_lower and 'th50' in subdir_lower:
        return i_base_th50
    elif 'base' in subdir_lower and 'th60' in subdir_lower:
        return i_base_th60
    elif 'base' in subdir_lower and 'th70' in subdir_lower:
        return i_base_th70
    elif 'base' in subdir_lower and 'ideal' in subdir_lower:
        return i_base_ideal
    elif 'cxl' in subdir_lower and 'nopam' in subdir_lower:
        return i_cxl_nopam
    elif 'cxl' in subdir_lower and 'pc_cnt' in subdir_lower:
        return i_cxl_pc_cnt
    elif 'cxl' in subdir_lower and 'th50' in subdir_lower:
        return i_cxl_th50
    elif 'cxl' in subdir_lower and 'th60' in subdir_lower:
        return i_cxl_th60
    elif 'cxl' in subdir_lower and 'th70' in subdir_lower:
        return i_cxl_th70
    elif 'cxl' in subdir_lower and 'ideal' in subdir_lower:
        return i_cxl_ideal

    else:
        #raise ValueError(f"Subdirectory name '{subdir}' does not match expected patterns.")
        print(subdir+" does not match expected patterns\n")
        return -1



def analyze_file(filename):
    # Initialize counters and accumulators
    ipc_values = []
    llc_misslat_values = []
    l2_misslat_values = []
    all_pam = false_positive = false_negative = 0
    llc_misses = 0

    # Compile regex patterns for faster matching
    ipc_pattern = re.compile(r'CPU \d+ cumulative IPC: (\d+\.\d+)')
    llc_misslat_pattern = re.compile(r'LLC AVERAGE MISS LATENCY: (\d+\.\d+)')
    l2_misslat_pattern = re.compile(r'(\w+)_L2C AVERAGE MISS LATENCY: (\d+\.\d+)')
    pam_pattern = re.compile(r'ALL_PAM: (\d+), False_positive: (\d+), Flase_negative: (\d+)')
    llc_misses_pattern = re.compile(r'LLC TOTAL\s+ACCESS:\s+\d+\s+HIT:\s+\d+\s+MISS:\s+(\d+)')

    with open(filename, 'r') as file:
        start_processing = False
        for line in file:
            # Skip lines until we find "Region"
            if 'Region' in line:
                start_processing = True
            if not start_processing:
                continue
            
            # Process lines for different formats
            if ipc_match := ipc_pattern.search(line):
                ipc_values.append(float(ipc_match.group(1)))
            elif llc_misslat_match := llc_misslat_pattern.search(line):
                llc_misslat_values.append(float(llc_misslat_match.group(1)))
            elif l2_misslat_match := l2_misslat_pattern.search(line):
                l2_misslat_values.append(float(l2_misslat_match.group(2)))
            elif pam_match := pam_pattern.search(line):
                all_pam += int(pam_match.group(1))
                false_positive += int(pam_match.group(2))
                false_negative += int(pam_match.group(3))
            elif llc_misses_match := llc_misses_pattern.search(line):
                llc_misses += int(llc_misses_match.group(1))

    # Calculate averages
    ipc_avg = sum(ipc_values) / len(ipc_values) if ipc_values else 0
    llc_misslat_avg = sum(llc_misslat_values) / len(llc_misslat_values) if llc_misslat_values else 0
    l2_misslat_avg = sum(l2_misslat_values) / len(l2_misslat_values) if l2_misslat_values else 0

    # Prepare results
    results = {
        'IPC': ipc_avg,
        'LLC_misslat': llc_misslat_avg,
        'L2_misslat': l2_misslat_avg,
        'all_pam': all_pam,
        'false_positive': false_positive,
        'false_negative': false_negative,
        'LLC_MISSES': llc_misses
    }

    return results

def analyze_benchmark(appname):
    ipcs = [0.0] * num_cfgs
    llc_mislats = [0.0] * num_cfgs
    l2_mislats = [0.0] * num_cfgs
    all_pam = [0] * num_cfgs
    false_positive = [0] * num_cfgs
    false_negative = [0] * num_cfgs
    LLC_misses = [0] * num_cfgs
    
  # Save current directory to revert back to it after the function is done
    original_directory = os.getcwd()

    try:
        # Change directory to the appname
        os.chdir(appname)

        # List all subdirectories in appname directory
        subdirs = next(os.walk('.'))[1]

        checked_cfgs = 0
        # Process each subdirectory
        for subdir in subdirs:
            # Construct the file path
            file_path = os.path.join(subdir, 'res.txt')

            index=get_custom_index(subdir)

            if(index!=-1):
                # Call analyze_file on the constructed file path
                results = analyze_file(file_path)
                checked_cfgs=checked_cfgs+1
                print(subdir)

            #print(subdir)
            
            if(index!=-1):
                # Store results in the respective lists
                ipcs[index] = results['IPC']
                llc_mislats[index] = results['LLC_misslat']
                l2_mislats[index] = results['L2_misslat']
                all_pam[index] = results['all_pam']
                false_positive[index] = results['false_positive']
                false_negative[index] = results['false_negative']
                LLC_misses[index] = results['LLC_MISSES']
    finally:
        # Change back to the original directory
        os.chdir(original_directory)

    print('checked_cfgs: '+str(checked_cfgs))
    # Return the results (optional, based on your requirement)
    return {
        'IPCs': ipcs,
        'LLC_misslats': llc_mislats,
        'L2_misslats': l2_mislats,
        'All_PAM': all_pam,
        'False_Positive': false_positive,
        'False_Negative': false_negative,
        'LLC_Misses': LLC_misses
    }




# Example usage:
#results = analyze_file('res.txt')
#results = analyze_benchmark('masstree')
#print(results)

f_ipcs = open("pam_ipcs.csv",'w')
f_llc_misslat = open("pam_llc_misslats.csv",'w')
f_l2_misslat = open("pam_l2_misslats.csv",'w')
f_all_pam = open("pam_all_counts.csv",'w')
f_false_pos = open("pam_false_pos.csv",'w')
f_false_neg = open("pam_false_neg.csv",'w')
f_llc_misses = open("pam_llc_misses.csv",'w')

original_dir = os.getcwd()
subdirs_top= next(os.walk('.'))[1]
#subdirs_top = ['ST_copy','BC','masstree','gcc']

    # Process each subdirectory
for subdir_top in subdirs_top:
    results = analyze_benchmark(subdir_top)
    print(results)
    sum_all_pam=[x+y for x,y in zip(sum_all_pam, results['All_PAM'])]
    sum_false_negative=[x+y for x,y in zip(sum_false_negative, results['False_Negative'])]
    sum_false_positive=[x+y for x,y in zip(sum_false_positive, results['False_Positive'])]
    f_ipcs.write(subdir_top+",")
    for i in range(num_cfgs):
        #f_ipcs.write(ipcs[i]+",")
        f_ipcs.write(str(results['IPCs'][i])+",")
    f_ipcs.write("\n")

    # Write LLC Miss Latencies
    f_llc_misslat.write(subdir_top + ",")
    for i in range(num_cfgs):
        f_llc_misslat.write(str(results['LLC_misslats'][i]) + ",")
    f_llc_misslat.write("\n")

    # Write L2 Miss Latencies
    f_l2_misslat.write(subdir_top + ",")
    for i in range(num_cfgs):
        f_l2_misslat.write(str(results['L2_misslats'][i]) + ",")
    f_l2_misslat.write("\n")

    # Write All PAM counts
    f_all_pam.write(subdir_top + ",")
    for i in range(num_cfgs):
        f_all_pam.write(str(results['All_PAM'][i]) + ",")
    f_all_pam.write("\n")

    # Write False Positives
    f_false_pos.write(subdir_top + ",")
    for i in range(num_cfgs):
        f_false_pos.write(str(results['False_Positive'][i]) + ",")
    f_false_pos.write("\n")

    # Write False Negatives
    f_false_neg.write(subdir_top + ",")
    for i in range(num_cfgs):
        f_false_neg.write(str(results['False_Negative'][i]) + ",")
    f_false_neg.write("\n")

    # Write LLC Misses
    f_llc_misses.write(subdir_top + ",")
    for i in range(num_cfgs):
        f_llc_misses.write(str(results['LLC_Misses'][i]) + ",")
    f_llc_misses.write("\n")


# Write All PAM counts
f_all_pam.write('Mean' + ",")
for i in range(num_cfgs):
    f_all_pam.write(str(sum_all_pam[i]) + ",")
f_all_pam.write("\n")

# Write False Positives
f_false_pos.write('Mean' + ",")
for i in range(num_cfgs):
    f_false_pos.write(str(sum_false_positive[i]) + ",")
f_false_pos.write("\n")

# Write False Negatives
f_false_neg.write('Mean' + ",")
for i in range(num_cfgs):
    f_false_neg.write(str(sum_false_negative[i]) + ",")
f_false_neg.write("\n")

# Close all files
f_ipcs.close()
f_llc_misslat.close()
f_l2_misslat.close()
f_all_pam.close()
f_false_pos.close()
f_false_neg.close()
f_llc_misses.close()

