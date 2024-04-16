import json

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


    trim_initial_values=int(len(float_list)*0.2)
    float_list=float_list[trim_initial_values:]
    avg_bw_per_logical_channel = 0
    if(len(float_list)==0):
        print("WARNING: NO BW VALUE READ")
    else:
        avg_bw_per_logical_channel = sum(float_list) / len(float_list)
        # bw per DDR5 channel is 2X (2 logical channels)
        avg_bw=avg_bw_per_logical_channel*2
        return avg_bw


avgBW = getavgBW('DDR5_baselineepoch.json')
print(str(avgBW))
