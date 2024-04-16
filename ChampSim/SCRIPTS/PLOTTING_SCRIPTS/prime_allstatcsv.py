import pandas as pd

# Load the CSV file
file_path = 'allstat.csv'
df = pd.read_csv(file_path)

# Define the list of names to match with
names_list = [
    "ST_copy", "ST_scale", "ST_add", "ST_triad",
    "Comp-sc", "Comp","CF", "PR-D", "BC", "PR", "Radii", "BFSCC", "BellmF", "BFS", "BFS-BV", "Triangle", "MIS",
    "fluida", "facesim", "raytrace", "scluster", "canneal",
    "lbm", "bwaves", "cactuB", "fotonik", "cam4", "wrf", "mcf", "roms", "pop2", "omnetpp", "xalanc", "gcc",
    "masstree", "kmeans"
]

# Replace 'NUM' or 'DIV/0' with 0
df.replace(['#NUM!', '#DIV/0!'], 0, inplace=True)

# Replace empty cells with 0 in all columns except the first
df.iloc[:, 1:] = df.iloc[:, 1:].replace('', 0).fillna(0)

# Function to find the closest match using basic string methods
def find_closest_name(name):
    # If the name is a number (like 0 for empty cells), or if it starts with 'GM', keep it as is
    if isinstance(name, (int, float)) or str(name).startswith('GM'):
        return name
    # Find the closest name by checking if the name is a substring of any name in the list
    for listed_name in names_list:
        if name in listed_name:
            return listed_name
    # If no match is found, return the original name
    return name

def fuzzy_match_name(original_name, names_list):
    # If the original name starts with 'GM' or is NaN, keep it as is
    if pd.isna(original_name) or str(original_name).startswith('GM'):
        return original_name
    
    # Remove common delimiters from the original name to aid in matching
    original_name_clean = original_name.replace('_', '').replace('-', '').lower()
    
    best_match = ''
    best_score = 0
    
    # Compare each name in the original list with every name in the names_list
    for name in names_list:
        score = 0
        name_clean = name.lower()
        i = 0
        
        # Calculate score based on characters in the abbreviated name found in the original name
        for char in name_clean:
            if char in original_name_clean[i:]:
                score += 1
                i = original_name_clean.index(char, i) + 1
            else:
                score -= 1
        
        # Update best match if this score is the highest
        if score > best_score:
            best_score = score
            best_match = name
    
    return best_match
# Apply the function to the first column
#df.iloc[:, 0] = df.iloc[:, 0].apply(find_closest_name)
df.iloc[:, 0] = df.iloc[:, 0].apply(lambda x: fuzzy_match_name(x, names_list))

# Convert 0 back to empty cells in the first column
df.iloc[:, 0] = df.iloc[:, 0].replace(0, '')
#
## Concatenate the sorted groups back into a single DataFrame
#sorted_df = pd.concat(sorted_groups).drop(['group_start', 'group_id'], axis=1)
# Make sure the 'Workload' column treats empty cells as empty strings
df['Workload'].fillna('', inplace=True)

# Find the indices where the 'Workload' column is empty; these are our group separators
separators = df[df['Workload'] == ''].index

# Initialize an empty DataFrame to hold the sorted groups, including separators
sorted_df_with_separators = pd.DataFrame(columns=df.columns)

# Iterate through each group, sort by 'speedup', and concatenate with separators
start_idx = 0
for end_idx in separators:
    group_df = df.iloc[start_idx:end_idx]
    if not group_df.empty and not group_df['Workload'].str.startswith('GM').any():
        group_df = group_df.sort_values(by='speedup', ascending=False)
    sorted_df_with_separators = pd.concat([sorted_df_with_separators, group_df])
    
    # Add the separator row itself
    if end_idx in df.index:
        sorted_df_with_separators = pd.concat([sorted_df_with_separators, df.loc[[end_idx]]])
    
    start_idx = end_idx + 1

# Handle the last group if it starts with 'GM'
if df.iloc[-1]['Workload'].startswith('GM'):
    group_df = df.iloc[start_idx:]
    sorted_df_with_separators = pd.concat([sorted_df_with_separators, group_df])

# Reset index in the resulting DataFrame
sorted_df_with_separators.reset_index(drop=True, inplace=True)

# Save the modified DataFrame to a new CSV file
output_file_path = 'modified_allstat.csv'
#df.to_csv(output_file_path, index=False)
sorted_df_with_separators.to_csv(output_file_path, index=False)

output_file_path

