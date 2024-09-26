#!/bin/bash

# Function to extract job name from log file
get_job_name() {
    # Extracting job name from the log file path
    job_name=$(basename "$1" | sed 's/\.log$//')
    echo "$job_name"
}

# Loop through each damaged job log file
grep -r -l "Error changing to scratch directory" | xargs grep -H -m 1 "Error changing to scratch directory" | cut -d ":" -f 1 | sort -u |
while IFS= read -r log_file; do
    # Extract job name from the log file
    job_name=$(get_job_name "$log_file")
    
    # Change directory to the folder containing the log file
    job_folder=$(dirname "$log_file")
    cd "$job_folder" || { echo "Failed to change directory to $job_folder. Skipping..."; continue; }
    
    # Check if the corresponding input file exists
    input_file="$job_name.inp"
    if [ -e "$input_file" ]; then
        # Rerun the job using gms_sbatch
        gms_sbatch -p trd -i "$input_file"
        echo "Rerunning job for $log_file"
    else
        echo "Input file not found for $log_file. Skipping..."
    fi
    
    # Return to the original directory
    cd - > /dev/null
done

