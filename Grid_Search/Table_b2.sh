#!/bin/bash

# Define the input and output files
input_file="final_energies_and_differences.txt"
output_file="sorted_energies_and_differences_by_folder.txt"

# Define the order of molecules in an array
declare -a molecule_order=("Heptazine" "Cyclazine" "Molecule3" "Molecule4" "Molecule5" "Molecule6" "Molecule7" "Molecule8" "Molecule9" "Molecule10")

# Clear the output file
> "$output_file"

# Extract folder types, sort and remove duplicates
folder_types=$(grep -oP 'a\d+_\d\.\d+_b\d+_\-?\d\.\d+_a\d+_\d\.\d+_b\d+_\-?\d\.\d+_S' "$input_file" | sort -u)

# Process each folder type
while read -r folder; do
    echo "Processing folder: $folder" >> "$output_file"
    # For each molecule in the order, process lines matching both the folder and molecule
    for molecule in "${molecule_order[@]}"; do
        grep "$folder" "$input_file" | grep "$molecule" | while read -r line; do
            # Extract S1 (previously Excitation Energy)
            s1=$(echo "$line" | grep -oP 'Excitation Energy = \K[\d.]+')
            # Corrected Extract T1 (previously Difference x -27.2114 value) to account for possible formatting variations
            t1=$(echo "$line" | grep -oP 'Difference x -27.2114 = \K[-+]?\d*\.?\d+')
            # Calculate the S1-T1 difference
            s1_minus_t1=$(echo "$s1 - $t1" | bc)
            # Output only the data without labels
            echo "$s1, $t1, $s1_minus_t1"
        done >> "$output_file"
    done
    echo "" >> "$output_file" # Add a blank line for readability between folders
done <<< "$folder_types"

echo "Data has been processed and saved to $output_file."

