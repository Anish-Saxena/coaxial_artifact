import os
import sys

def getavgBW(filename):

    float_list = []

    #print("I'm not ready yet")
    with open(filename) as f:
        for line in f:
            #print("does this go through once?")
            #data = json.loads(line)
            #if "average_bandwidth" in data:
            #    value = float(data["average_bandwidth"])
            #    float_list.append(value)
            tmp=line.split('"average_bandwidth":')[1]
            tmp=tmp.split(',')[0]
            #print(tmp)
            value = float(tmp)
            float_list.append(value)


    trim_initial_values=int(len(float_list)*0.1)
    float_list=float_list[trim_initial_values:]
    avg_bw_per_logical_channel = 0
    if(len(float_list)==0):
        print("WARNING: NO BW VALUE READ")
    else:
        avg_bw_per_logical_channel = sum(float_list) / len(float_list)
        # bw per DDR5 channel is 2X (2 logical channels)
        avg_bw=avg_bw_per_logical_channel*2
        return avg_bw

def read_values(filename):
    with open(filename, 'r') as file:
        # Find the line that includes 'Region of Interest'
        for line in file:
            if 'Region of Interest' in line:
                break
        # Read the next five lines as floats
        values = []
        ipc_sum=0.0;
        ipc_n=0;
        lat_sum=0.0;
        lat_n=0;
        avg_ipc=0
        avg_lat=0
        l2c_lat=0
        l2c_misses=0
        all_pam = 0
        pam_ratio =0
        
        while line:
            if 'IPC' in line:
                index=line.index('IPC:')
                ipc_str=line[index+5:].strip()
                ipc_str=ipc_str.split(' ')[0]
                ipc_float=float(ipc_str)
                ipc_sum=ipc_sum+ipc_float
                ipc_n=ipc_n+1
            #if 'LLC AVERAGE MISS LATENCY:' in line:
            if 'cpu0_L2C AVERAGE MISS LATENCY:' in line:
                tokens = line.split()
                # Find the index of the token 'LATENCY:'
                index = tokens.index('LATENCY:')
                # Extract the value after 'LATENCY:' as a string
                latency_str = tokens[index+1]
                #print(latency_str)
                # Convert the string to a float
                latency_float = float(latency_str)
                lat_sum=lat_sum + latency_float
                lat_n=lat_n+1
                l2c_lat=latency_float
                line=file.readline()
                if('ALL_PAM' not in line):
                    print('Missing ALL_PAM line')
                tmp=line.split(',')[0]
                tmp=tmp.split(':')[1]
                all_pam = int(tmp)

            if 'cpu0_L2C TOTAL' in line:
                misses_str = line.split('MISS:')[1]
                #dbg
                #print(misses_str)
                l2c_misses=int(misses_str)
                           

            #line=next(file)
            line=file.readline()

        if(l2c_misses==0):
            print("WARNING - 0 l2misses?")
        else:
            pam_ratio = all_pam*100 / l2c_misses

        if(ipc_n==0):
            print("WARNING - run didn't finish")
        elif(lat_n==0):
            #print('ipc_n: '+str(ipc_n))
            print("WARNING - run didn't finish")
        else:
            avg_ipc = ipc_sum / ipc_n
            avg_lat = lat_sum / lat_n
        values.append(avg_ipc)
        values.append(avg_lat)
        values.append(l2c_lat)
        values.append(pam_ratio)
    return values


def collect_stats(calling_dir, outfile):
  """
  Collects statistics from Baseline_ and CXL_ directories and writes them to a CSV file.

  Args:
    calling_dir: The directory from which the script is called.
    outfile: The name of the output CSV file.
  """

  # Write header row
  with open(outfile, 'w') as f:
    f.write("app, DDRIPC,CXLIPC,DDRLAT,CXLLAT,DDRBW,CXLBW\n")

  for dir in os.listdir(calling_dir):
    if dir.startswith("Baseline_"):
      app_name = dir[9:]  # Remove "Baseline_" prefix
      baseline_dir = os.path.join(calling_dir, dir)

      # Collect stats from Baseline directory
      baseline_stats = read_values(os.path.join(baseline_dir, "res.txt"))
      ddr_ipc = baseline_stats[0]
      ddr_lat = baseline_stats[1]
      ddr_bw = getavgBW(os.path.join(baseline_dir, "DDR5_baselineepoch.json"))

      # Find corresponding CXL directory
      cxl_dir = os.path.join(calling_dir, f"CXL_{app_name}")

      if os.path.isdir(cxl_dir):
        # Collect stats from CXL directory
        cxl_stats = read_values(os.path.join(cxl_dir, "res.txt"))
        cxl_ipc = cxl_stats[0]
        cxl_lat = cxl_stats[1]
        cxl_bw = getavgBW(os.path.join(cxl_dir, "DDR5_baselineepoch.json")) * 4

        # Write data to CSV file
        with open(outfile, 'a') as f:
          f.write(f"{app_name}, {ddr_ipc}, {cxl_ipc}, {ddr_lat}, {cxl_lat}, {ddr_bw}, {cxl_bw}\n")



collect_stats(os.getcwd(), "collected_stats.csv")
