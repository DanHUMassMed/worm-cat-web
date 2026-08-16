#!/bin/bash

# Output CSV file
output_file="output.csv"

# Write CSV header
echo "runtime,annotation_version,input_type" > "$output_file"

# Find all run_data.txt files
find . -name "run_data.txt" | while read filepath; do
    # Extract the data from each run_data.txt
    runtime=$(grep "^runtime:" "$filepath" | cut -d':' -f2-)
    annotation_version=$(grep "^annotation_version:" "$filepath" | cut -d':' -f2-)
    input_type=$(grep "^input_type:" "$filepath" | cut -d':' -f2-)

    # Remove any leading or trailing spaces
    runtime=$(echo "$runtime" | xargs)
    annotation_version=$(echo "$annotation_version" | xargs)
    input_type=$(echo "$input_type" | xargs)

    # Append the extracted data to the CSV file
    echo "$runtime,$annotation_version,$input_type" >> "$output_file"
done

echo "CSV file created: $output_file"
