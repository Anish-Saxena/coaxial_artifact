import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import matplotlib.patches as mpatches
# Define font sizes and bar configurations
axis_title_size = 16
legend_size = 14
tick_label_size = 14
bar_width = 0.07
#colors = ['skyblue', 'lightgreen', 'orange']  # Colors for the stacks
#colors=['#DDA0DD','#8FBC8F','#FAA460','#CD5C5C','#9370DB','#6495ED','#66CDAA']
#colors=['#DDA0DD', '#A89AE4', '#ABBFB0','#799A82','#3D5A45', '#6495ED']
colors=['#4F000B','#720026','#CE4257','#FF7F51','#FF9B54', '#F3A6C2','#C26989','#913B59','#602F40']
colors2=['black','#304837', '#3D5A45','#799A82','#ABBFB0','black','black']
colors3 = ['black','#42347E','#7C67D6','#A89AE4','lavender','black']

colors=[colors2[3],'#FFA500','lavender']
#colors=[colors2[3],'#FFA500','grey']
#hatch_pattern = ''  # No hatch pattern for the first half of bars
hatchpat='\\\\'
hatches=['//','','XX']
alpha_val=1

# Read the CSV files
all_counts_df = pd.read_csv('pam_all_counts.csv', header=None).set_index(0)
false_pos_df = pd.read_csv('pam_false_pos.csv', header=None).set_index(0)
false_neg_df = pd.read_csv('pam_false_neg.csv', header=None).set_index(0)
#llc_misses_df = pd.read_csv('pam_llc_misses.csv', header=None).set_index(0)
llc_misses_df = all_counts_df.add(false_neg_df, fill_value=0)
# Fill NaN values with 0
all_counts_df.fillna(0, inplace=True)
false_pos_df.fillna(0, inplace=True)
false_neg_df.fillna(0, inplace=True)
llc_misses_df.fillna(0, inplace=True)

# It's important to ensure that there are no zero values in llc_misses_df
# to avoid division by zero. Replace zero with NaN in llc_misses_df and then forward fill.
llc_misses_df.replace(0, np.nan, inplace=True)
llc_misses_df.fillna(method='ffill', inplace=True)

# Normalize the counts by llc_misses values
sum_three_bars = all_counts_df+false_neg_df- false_pos_df
norm_all_counts = all_counts_df.div(sum_three_bars.values)
norm_false_pos = false_pos_df.div(sum_three_bars.values)
norm_false_neg = false_neg_df.div(sum_three_bars.values)

# Fill NaN values with 0
norm_all_counts.fillna(0, inplace=True)
norm_false_pos.fillna(0, inplace=True)
norm_false_neg.fillna(0, inplace=True)


#######manually adding mean for all apps, instead of just the few apps here
## Calculate the mean for each configuration
#mean_all_counts = norm_all_counts.mean()
#mean_false_pos = norm_false_pos.mean()
#mean_false_neg = norm_false_neg.mean()
#
## Append the means as new rows
#norm_all_counts.loc['Mean'] = mean_all_counts
#norm_false_pos.loc['Mean'] = mean_false_pos
#norm_false_neg.loc['Mean'] = mean_false_neg
#




# Calculate the bottom for the stack
bottom_stack = norm_all_counts - norm_false_pos

# Plotting
fig, ax = plt.subplots(figsize=(10, 4))
index = np.arange(norm_all_counts.shape[0])  # X-axis indexes for benchmarks

for i in range(norm_all_counts.shape[1]):
    alpha_val = 1
    if i >= norm_all_counts.shape[1] / 2:
        hatchpat = ''  # Apply hatch pattern for the second half of bars
        alpha_val=1  # Apply gradient for the second half of bars

    # Bottom stack (all_counts - false_pos)
    ax.bar(index + i * bar_width, bottom_stack.iloc[:, i], bar_width,
           color=colors[0], edgecolor='black', label='Valid Parallel Accesses' if i == 0 else "", alpha=alpha_val, hatch=hatchpat)
    
    # Middle stack (false_pos)
    ax.bar(index + i * bar_width, norm_false_neg.iloc[:, i], bar_width,
           bottom=bottom_stack.iloc[:, i],
           color=colors[1], edgecolor='black', label='False Negatives' if i == 0 else "", alpha=alpha_val, hatch=hatchpat)
    
    # Top stack (false_neg)
    ax.bar(index + i * bar_width, norm_false_pos.iloc[:, i], bar_width,
           bottom=bottom_stack.iloc[:, i] + norm_false_neg.iloc[:, i],
           color=colors[2], edgecolor='black', label='False Positives' if i == 0 else "", alpha=alpha_val, hatch=hatchpat)

# Set the benchmark names as x-ticks
ax.set_xticks(index + bar_width * (norm_all_counts.shape[1] - 1) / 2)
ax.set_xticklabels(norm_all_counts.index, rotation=0, ha="center", fontsize=tick_label_size)

# Adding labels and title
#plt.ylabel('Normalized Counts', fontsize=axis_title_size)
plt.ylabel('Concurrent LLC/mem \naccess type, norm. to ideal', fontsize=axis_title_size)
ax.yaxis.grid(True)
ax.set_ylim([0,1.5])
# Define custom labels (only if the legend is not already descriptive enough)
#config_labels = ['None', 'MAP-I', 'RLB50%', 'RLB60%', 'RLB70%', 'Ideal']
legend_colors = ['white','white',colors[0],colors[1],colors[2]]
legend_hatches=['\\\\','']+[None]*3
# Create the legend with a specific fontsize
#custom_handles = [mpatches.Patch(facecolor=color, edgecolor='black', hatches=) for color in legend_colors]
custom_handles = [mpatches.Patch(facecolor=legend_colors[i], edgecolor='black', hatch=legend_hatches[i]) for i in range(len(legend_colors))]
labels = [ 'Baseline','CoaXiaL','Valid concurrent access','False Negatives','False Positives']
ax.legend(custom_handles, labels, fontsize=legend_size, ncol=3)
#ax.legend(custom_handles,frameon=True, loc='best', fontsize=legend_size)

# Set the fontsize for the y-tick labels
ax.tick_params(axis='y', labelsize=tick_label_size)

# Show the plot with a tight layout
plt.tight_layout()
plt.savefig('pam_breakdown.png', bbox_inches='tight')
plt.savefig('pam_breakdown.pdf', bbox_inches='tight')

