#!/bin/bash

# Define the expected molecule names
declare -a expected_molecules=("Heptazine" "Cyclazine" "Molecule3" "Molecule4" "Molecule5" "Molecule6" "Molecule7" "Molecule8" "Molecule9" "Molecule10")

# Path to the file containing folder info
file_path="sorted_energies_and_differences_by_folder.txt"

# Initialize variables
current_folder=""
current_molecules=()

# Function to rerun files in a folder (both S and T folders)
rerun_inp_files() {
    local folder=$1
    local missing_molecules=("${!2}")

    for molecule in "${missing_molecules[@]}"; do
        # Search for the .inp files that contain the molecule name but avoid duplicate folder names in the search
        inp_file=$(find "$folder" -type f -name "*${molecule}*.inp" 2>/dev/null)
        
        if [[ -n $inp_file ]]; then
            echo "Rerunning file '$inp_file' for molecule '$molecule' in folder '$folder'"
            # Navigate to the folder where the .inp file is located and run the command
            (cd "$folder" && gms_sbatch -p xeon,trd,ryzn,r630 -c 30 -i "$(basename "$inp_file")")
        else
            echo "No .inp file found for molecule '$molecule' in folder '$folder'"
        fi
    done
}

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

                # Run in the '_S' folder
                rerun_inp_files "$current_folder" missing_molecules[@]

                # Find corresponding '_T' folder by replacing '_S' with '_T'
                t_folder="${current_folder%_S}_T"
                if [[ -d $t_folder ]]; then
                    rerun_inp_files "$t_folder" missing_molecules[@]
                else
                    echo "Corresponding T folder '$t_folder' does not exist."
                fi
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

        # Run in the '_S' folder
        rerun_inp_files "$current_folder" missing_molecules[@]

        # Find corresponding '_T' folder by replacing '_S' with '_T'
        t_folder="${current_folder%_S}_T"
        if [[ -d $t_folder ]]; then
            rerun_inp_files "$t_folder" missing_molecules[@]
        else
            echo "Corresponding T folder '$t_folder' does not exist."
        fi
    fi
fi

