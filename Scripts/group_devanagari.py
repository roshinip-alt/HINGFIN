import csv
from pathlib import Path

# ---------------------------------------------------------
# File locations
# ---------------------------------------------------------

# This script is located in:
# StockMarket/Scripts/group_devanagari.py

script_dir = Path(__file__).resolve().parent

dictionary_file = script_dir.parent / "Dataset" / "ticker_dictionary.tsv"
temp_file = script_dir.parent / "Dataset" / "ticker_dictionary_temp.tsv"


# ---------------------------------------------------------
# Read the existing ticker dictionary
# ---------------------------------------------------------

with open(dictionary_file, "r", encoding="utf-8", newline="") as f:
    rows = list(csv.reader(f, delimiter="\t"))

header = rows[0]
data_rows = rows[1:]


# ---------------------------------------------------------
# Separate Devanagari rows from other rows
# ---------------------------------------------------------

devanagari_rows = {}
normal_rows = []

for row in data_rows:

    # A valid dictionary row should have at least 4 columns
    if len(row) >= 4 and row[2] == "devanagari":

        symbol = row[0]

        # Store the Devanagari row using its symbol
        devanagari_rows[symbol] = row

    else:
        normal_rows.append(row)


# ---------------------------------------------------------
# Rebuild the dictionary
# ---------------------------------------------------------

grouped_rows = []

for i, row in enumerate(normal_rows):

    grouped_rows.append(row)

    current_symbol = row[0]

    # Check whether the next normal row belongs
    # to a different company.
    is_last_row_for_symbol = (
        i == len(normal_rows) - 1
        or normal_rows[i + 1][0] != current_symbol
    )

    # When we reach the end of a company's existing rows,
    # add its Devanagari row immediately after them.
    if is_last_row_for_symbol and current_symbol in devanagari_rows:

        grouped_rows.append(devanagari_rows[current_symbol])


# ---------------------------------------------------------
# Write the reordered dictionary to a temporary file
# ---------------------------------------------------------

with open(temp_file, "w", encoding="utf-8", newline="") as f:

    writer = csv.writer(
        f,
        delimiter="\t",
        lineterminator="\n"
    )

    writer.writerow(header)
    writer.writerows(grouped_rows)


# ---------------------------------------------------------
# Replace the original file
# ---------------------------------------------------------

temp_file.replace(dictionary_file)


print("Devanagari rows grouped with their corresponding companies.")
print(f"Total Devanagari rows: {len(devanagari_rows)}")