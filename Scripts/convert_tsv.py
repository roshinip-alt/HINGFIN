import pandas as pd

input_file = "../Dataset/NIFTY50.csv"
output_file = "../Dataset/NIFTY50.tsv"

df = pd.read_csv(input_file)

df.to_csv(output_file, sep="\t", index=False)

print("NIFTY50.tsv created successfully!")
print(df.head())