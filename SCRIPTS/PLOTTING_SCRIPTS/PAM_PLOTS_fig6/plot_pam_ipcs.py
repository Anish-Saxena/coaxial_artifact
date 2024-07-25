import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gmean
import matplotlib.patches as mpatches



# Define font sizes
axis_title_size = 16
legend_size = 14
tick_label_size = 14

# Read the CSV file
df = pd.read_csv('pam_ipcs.csv', header=None)

# Set the benchmark names as the index
df.set_index(0, inplace=True)

# Normalize each row by the first value in that row
df_normalized = df.div(df.iloc[:, 0], axis=0)

# Predefined colors for the first and second half of bars
#first_half_colors = 'orange'
#second_half_colors = 'skyblue'


##### removing geomean bit: Manually added geomean, \
   ## since I need geomean from ALL APPS, not just these few
#geo_means = df_normalized.apply(gmean, axis=0)

# Append the geometric means as an extra row
#df_normalized.loc['GeoMean'] = geo_means

#colors=['#DDA0DD','#8FBC8F','#FAA460','#CD5C5C','#9370DB','#6495ED','#66CDAA']
#colors=['#DDA0DD', '#A89AE4', '#ABBFB0','#799A82','#3D5A45', '#6495ED']
#colors=['#A89AE4','#7C67D6','#42347E', '#F3A6C2','#C26989','#913B59','#602F40']
#colors=['#A89AE4','#7C67D6','#42347E', '#4F000B','#720026','#CE4257','#FF7F51','#FF9B54']
#colors=['#4F000B','#720026','#CE4257','#FF7F51','#FF9B54', '#F3A6C2','#C26989','#913B59','#602F40']
#colors=['#4F000B','#720026','#CE4257','#FF7F51','#FFCD70', '#F3A6C2', 'white','white']
colors=['#dda0dd','lightyellow', '#8fbc8f', '#faa460', '#9370db','grey', 'white','white']
# Plotting
fig, ax = plt.subplots(figsize=(10,4))

# Get the number of benchmarks and configurations
num_benchmarks = df_normalized.shape[0]
num_configs = df_normalized.shape[1]
print(num_configs)
bar_width = 0.07

# Create an index for the benchmarks
index = np.arange(num_benchmarks)

# Plot each set of bars for each benchmark
for i in range(num_configs):
    # Use a different color for the second half of the bars
    #color = first_half_colors if i < (num_configs / 2 -1) else second_half_colors
    hatchpat = '\\\\' if i < (num_configs / 2 -1) else ''
    color = colors[i%(6)]
    add_space = 0
    if (i >= (num_configs / 2 -1)):
        add_space = bar_width*0.7

    # Plotting the bars
    ax.bar(index + i * bar_width+add_space, df_normalized.iloc[:, i], bar_width, label=f'Config {i+1}', color=color, edgecolor='black', hatch=hatchpat)

# Add the benchmark names as x-ticks
ax.set_xticks(index + bar_width * (num_configs - 1) / 2)
ax.set_xticklabels(df_normalized.index, rotation=0, ha="center", fontsize=tick_label_size)
ax.yaxis.set_major_locator(plt.MultipleLocator(0.5))
# Adding labels and title
#plt.xlabel('Benchmark', fontsize=axis_title_size)
plt.ylabel('Normalized IPCs', fontsize=axis_title_size)
ax.yaxis.grid(True)

# Define custom labels
#config_labels = ['None', 'MAP-I', 'RLB50%', 'RLB6CALM, 'RLB70%', 'Ideal']
hatches = [None] * 6 + ['\\\\','']  # No hatch for all except CoaXiaL
#colors=['#4F000B','#720026','#CE4257','#FF7F51','#FF9B54', '#F3A6C2','white','white']
#colors=['#4F000B','#720026','#CE4257','#FF7F51','#FFCD70', '#F3A6C2', 'white','white']
config_labels = ['Serial access', 'MAP-I', 'CALM50%', 'CALM60%', 'CALM70%', 'Ideal', 'Baseline', 'CoaXiaL']
# Create custom handles for the legend
#custom_handles = [plt.Line2D([], [], linestyle="", marker='')] * len(config_labels)
custom_handles = [mpatches.Patch(facecolor=colors[i], label=config_labels[i], hatch=hatches[i], edgecolor='black') for i in range(len(config_labels))]
# Create the legend with a specific fontsize
#ax.legend(custom_handles, config_labels, frameon=True, handlelength=0, handletextpad=0, loc='upper right', fontsize=legend_size)
ax.legend(custom_handles, config_labels, frameon=True, loc='upper right', fontsize=legend_size, handlelength=2, ncol=2)
# Set the fontsize for the y-tick labels
ax.tick_params(axis='y', labelsize=tick_label_size)

# Show the plot with a tight layout
plt.tight_layout()
plt.savefig('pam_speedup.png', bbox_inches='tight')
plt.savefig('pam_speedup.pdf', bbox_inches='tight')



