#!/bin/bash

# Define the expected molecule names
declare -a expected_molecules=("Heptazine" "Cyclazine" "Molecule3" "Molecule4" "Molecule5" "Molecule6" "Molecule7" "Molecule8" "Molecule9" "Molecule10")

# Path to the file containing folder info
file_path="sorted_energies_and_differences_by_folder.txt"

# Initialize variables
current_folder=""
current_molecules=()

# Process the input file line by line
while IFS= read -r line; do
    # Check if line specifies a folder
    if [[ $line == "Processing folder:"* ]]; then
        # If current folder has been processed, check for missing molecules
        if [[ -n $current_folder ]]; then
            missing_molecules=()
            for molecule in "${expected_molecules[@]}"; do
                if [[ ! " ${current_molecules[@]} " =~ " ${molecule} " ]]; then
                    missing_molecules+=("$molecule")
                fi
            done

            # If there are missing molecules, rerun the .inp file(s) containing the molecule name
            if [[ ${#missing_molecules[@]} -gt 0 ]]; then
                echo "In folder '$current_folder', the following molecules are missing: ${missing_molecules[*]}"
                cd "$current_folder" || continue
                for molecule in "${missing_molecules[@]}"; do
                    # Find the .inp file containing the molecule name
                    inp_file=$(ls *"${molecule}"*.inp 2>/dev/null)
                    if [[ -n $inp_file ]]; then
                        echo "Rerunning file '$inp_file' for molecule '$molecule'"
                        gms_sbatch -p xeon,trd,ryzn,r630 -c 30 -i "$inp_file"
                    else
                        echo "No .inp file found for molecule '$molecule' in '$current_folder'"
                    fi
                done
                cd - || exit
            fi
        fi

        # Start processing the new folder
        current_folder=$(echo "$line" | cut -d':' -f2 | xargs)
        current_molecules=()

    # Otherwise, it's a molecule entry
    else
        molecule_name=$(echo "$line" | cut -d',' -f1 | xargs)
        current_molecules+=("$molecule_name")
    fi
done < "$file_path"

# Check the last folder if necessary
if [[ -n $current_folder ]]; then
    missing_molecules=()
    for molecule in "${expected_molecules[@]}"; do
        if [[ ! " ${current_molecules[@]} " =~ " ${molecule} " ]]; then
            missing_molecules+=("$molecule")
        fi
    done

    # Rerun the .inp file(s) for the missing molecules
    if [[ ${#missing_molecules[@]} -gt 0 ]]; then
        echo "In folder '$current_folder', the following molecules are missing: ${missing_molecules[*]}"
        cd "$current_folder" || exit
        for molecule in "${missing_molecules[@]}"; do
            # Find the .inp file containing the molecule name
            inp_file=$(ls *"${molecule}"*.inp 2>/dev/null)
            if [[ -n $inp_file ]]; then
                echo "Rerunning file '$inp_file' for molecule '$molecule'"
                gms_sbatch -p xeon,trd,ryzn,r630 -c 30 -i "$inp_file"
            else
                echo "No .inp file found for molecule '$molecule' in '$current_folder'"
            fi
        done
        cd - || exit
    fi
fi

