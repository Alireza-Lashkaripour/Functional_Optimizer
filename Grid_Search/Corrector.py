#!/bin/bash

# Iterate over each subdirectory of the current directory
for subdir in */; do
    echo "Entering directory: $subdir"
    cd "$subdir"
    # Check each .inp file to see if a corresponding .log file exists
    for inpfile in *.inp; do
        if [[ ! -e "${inpfile%.inp}.log" ]]; then
            echo "No log file for $inpfile, running gms_sbatch..."
            gms_sbatch -p r630 -c 30 -i "$inpfile"
        else
            echo "Log file exists for $inpfile, skipping..."
        fi
    done
    cd ..
done

