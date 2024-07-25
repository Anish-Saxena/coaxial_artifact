import csv
import pickle

# Open the CSV file for reading
with open('allstats.csv', 'r') as csv_file:
    # Use the csv module to parse the file
    csv_reader = csv.reader(csv_file)
    # Get the headers and initialize empty lists for each column
    headers = next(csv_reader)
    columns = [[] for _ in range(len(headers))]
    # Loop through each row and add the values to the appropriate list
    for row in csv_reader:
        for i, value in enumerate(row):
            # Convert the value to a float if possible, otherwise leave it as a string
            try:
                value = float(value)
            except ValueError:
                pass
            columns[i].append(value)

# Save each column to a separate pickle file
for i, header in enumerate(headers):
    with open(f'{header}.pkl', 'wb') as pickle_file:
        pickle.dump(columns[i], pickle_file)
