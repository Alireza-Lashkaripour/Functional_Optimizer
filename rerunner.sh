#!/bin/bash

# Function to search and rerun the .inp file if the conditions are met
rerun_inp_if_needed() {
    local log_file="$1"
    local inp_file="${log_file%.log}.inp"
    local inp_dir=$(dirname "$inp_file")

    # Check if the log file contains any of the search phrases
#    if grep -qE "directory named above must exist on all nodes|directory DDI Process 138: Multiple DDI processes connecting with the same rank.must be writeable|if using ddikick.x, specify -scr directory" "$log_file"; then
#    if grep -qE "DDI Process 138: Multiple DDI processes connecting with the same rank." "$log_file"; then
    if grep -qE "Initiating 152 compute processes on 1 nodes to run the following command" "$log_file"; then   
        echo "Found required string in $log_file. Rerunning corresponding .inp file: $inp_file"
        
        # Change to the directory where the .inp file is located
        cd "$inp_dir" || exit
        
        # Rerun the corresponding .inp file with the specified command
        gms_sbatch -p trd,ryzn,chc3,r630 -c 30 -i "$(basename "$inp_file")"
        
        # Change back to the original directory
        cd - > /dev/null
    fi
}

# Export the function to be available for subprocesses
export -f rerun_inp_if_needed

# Find all .log files in all directories and subdirectories
find . -type f -name "*.log" -exec bash -c 'rerun_inp_if_needed "$0"' {} \;

echo "Script execution completed."
