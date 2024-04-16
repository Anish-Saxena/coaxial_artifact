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
        
        while line:
            if 'IPC' in line:
                index=line.index('IPC:')
                ipc_str=line[index+5:].strip()
                ipc_str=ipc_str.split(' ')[0]
                ipc_float=float(ipc_str)
                ipc_sum=ipc_sum+ipc_float
                ipc_n=ipc_n+1
            if 'LLC AVERAGE MISS LATENCY:' in line:
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

            #line=next(file)
            line=file.readline()

        avg_ipc = ipc_sum / ipc_n
        avg_lat = lat_sum / lat_n
        values.append(avg_ipc)
        values.append(avg_lat)
    return values


stats=read_values('res.txt')
print(stats)
