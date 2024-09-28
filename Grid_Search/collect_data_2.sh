#!/bin/bash

# Output file
output_file="final_energies_and_differences.txt"
# Ensure the output file is empty before starting
> "$output_file"

# Find all directories ending with '_S'
for dir_s in *_S; do
    # Determine the corresponding '_T' directory by replacing '_S' with '_T'
    dir_t="${dir_s/_S/_T}"

    # Check if the corresponding '_T' directory exists
    if [[ -d "$dir_t" ]]; then
        echo "Processing $dir_s and $dir_t..."

        # Process each .log file in the _S directory
        for log_file_s in "$dir_s"/*.log; do
            filename=$(basename "$log_file_s")
            base_name="${filename%.log}"  # Remove .log extension

            # Extract values from the _S file
            read energy_a_s excitation_energy_s <<< $(awk '/1  A/ {energy_a=$3} /1  ->  2/ {excitation_energy=$4; exit} END {print energy_a, excitation_energy}' "$log_file_s")

            # Corresponding file in the _T directory
            log_file_t="${dir_t}/${base_name/_S/_T}.log"
            if [[ -f "$log_file_t" ]]; then
                energy_a_t=$(awk '/1  A/ {print $3; exit}' "$log_file_t")

                if [[ -n "$energy_a_s" && -n "$energy_a_t" && -n "$excitation_energy_s" ]]; then
                    # Calculate the difference and multiply by -27.2114
                    difference=$(echo "($energy_a_s - $energy_a_t) * -27.2114" | bc)

                    # Write the extracted values and calculated difference to the output file
                    echo "$base_name: Excitation Energy = $excitation_energy_s, Energy_A_S = $energy_a_s, Energy_A_T = $energy_a_t, Difference x -27.2114 = $difference" >> "$output_file"
                fi
            fi
        done
    else
        echo "Corresponding directory $dir_t does not exist."
    fi
done

echo "Final energies and differences have been saved to $output_file."

