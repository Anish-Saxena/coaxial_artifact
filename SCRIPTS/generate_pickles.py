import pandas as pd
import pickle

def generate_pickles(input_file):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_file)

    # Iterate through each column (excluding the 'app' column)
    for column in df.columns:
        # Construct the output pickle file name
        output_file = f"{column.strip()}.pkl"

        # Get the column data and serialize it to a pickle file
        with open(output_file, 'wb') as f:
            pickle.dump(df[column].tolist(), f)

if __name__ == "__main__":
    input_file = 'collected_stats.csv'
    generate_pickles(input_file)

