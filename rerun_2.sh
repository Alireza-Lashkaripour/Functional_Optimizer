#!/bin/bash

# Function to extract job name from log file
get_job_name() {
    # Extracting job name from the log file path
    job_name=$(basename "$1" | sed 's/\.log$//')
    echo "$job_name"
}

# Maximum number of concurrent jobs
max_jobs=1000

# Job counter
job_count=0

# Job IDs list
job_ids=()

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
        job_id=$(gms_sbatch -p trd -i "$input_file" | awk '{print $4}')
        job_ids+=("$job_id")

        ((job_count++))

        # Check if we've reached the max jobs limit for the trd partition
        if ((job_count == max_jobs)); then
            echo "Max job count reached on trd. Waiting for all jobs to finish before submitting more..."

            # Wait for all jobs to finish
            for id in "${job_ids[@]}"; do
                while true; do
                    # Check specifically for jobs in the trd partition
                    jobs_running=$(squeue -u "$USER" -p trd -j "$id" | wc -l)

                    if ((jobs_running == 1)); then
                        break
                    fi

                    sleep 60
                done
            done

            # Reset job counter and job IDs list for the next batch
            job_count=0
            job_ids=()
            echo "Batch of jobs completed on trd. Proceeding to the next batch..."
        fi

        echo "Rerunning job for $log_file"
    else
        echo "Input file not found for $log_file. Skipping..."
    fi

    # Return to the original directory
    cd - > /dev/null
done

# Implement a final wait for any remaining jobs specifically on trd if the last batch was not exactly $max_jobs
if ((job_count > 0)); then
    echo "Final batch on trd. Waiting for remaining jobs to complete..."

    for id in "${job_ids[@]}"; do
        while true; do
            jobs_running=$(squeue -u "$USER" -p trd -j "$id" | wc -l)

            if ((jobs_running == 1)); then
                break
            fi

            sleep 60
        done
    done

    echo "All jobs on trd have been completed."
fi
