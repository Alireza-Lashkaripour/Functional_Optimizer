#!/bin/bash

rerun_inp_if_needed() {
    local log_file="$1"
    local inp_file="${log_file%.log}.inp"
    local inp_dir=$(dirname "$inp_file")

    # Check if the log file contains any of the search phrases
#    if grep -qE "directory named above must exist on all nodes|directory DDI Process 138: Multiple DDI processes connecting with the same rank.must be writeable|if using ddikick.x, specify -scr directory" "$log_file"; then
#    if grep -qE "DDI Process 138: Multiple DDI processes connecting with the same rank." "$log_file"; then
    if grep -qE "Initiating 152 compute processes on 1 nodes to run the following command" "$log_file"; then   
        echo "Found required string in $log_file. Rerunning corresponding .inp file: $inp_file"
        
        cd "$inp_dir" || exit
        
        gms_sbatch -p trd,ryzn,chc3,r630 -c 30 -i "$(basename "$inp_file")"
        
        cd - > /dev/null
    fi
}

export -f rerun_inp_if_needed

find . -type f -name "*.log" -exec bash -c 'rerun_inp_if_needed "$0"' {} \;

echo "Script Execution Completed."
