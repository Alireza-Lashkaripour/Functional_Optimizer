#!/bin/bash

# Maximum number of concurrent jobs
max_jobs=100

# Job counter
job_count=0

# Job IDs list
job_ids=()

# Iterate over each subdirectory of the current directory
for subdir in */; do
    echo "Entering directory: $subdir"
    cd "$subdir"

    # Check each .inp file to see if a corresponding .log file exists
    for inpfile in *.inp; do
        if [[ ! -e "${inpfile%.inp}.log" ]]; then
            echo "No log file for $inpfile, running gms_sbatch..."

            # Submit the job to r630 partition and capture the job ID
            job_id=$(gms_sbatch -p trd -i "$inpfile" | awk '{print $4}')
            job_ids+=("$job_id")

            ((job_count++))

            # Check if we've reached the max jobs limit for the r630 partition
            if ((job_count == max_jobs)); then
                echo "Max job count reached on r630. Waiting for all jobs to finish before submitting more..."

                # Wait for all jobs to finish
                for id in "${job_ids[@]}"; do
                    while true; do
                        # Check specifically for jobs in the r630 partition
                        jobs_running=$(squeue -u "$USER" -p r630 -j "$id" | wc -l)

                        if ((jobs_running == 1)); then
                            break
                        fi

                        sleep 60
                    done
                done

                # Reset job counter and job IDs list for the next batch
                job_count=0
                job_ids=()
                echo "Batch of jobs completed on r630. Proceeding to the next batch..."
            fi
        else
            echo "Log file exists for $inpfile, skipping..."
        fi
    done

    cd ..
done

# Implement a final wait for any remaining jobs specifically on r630 if the last batch was not exactly $max_jobs
if ((job_count > 0)); then
    echo "Final batch on r630. Waiting for remaining jobs to complete..."

    for id in "${job_ids[@]}"; do
        while true; do
            jobs_running=$(squeue -u "$USER" -p r630 -j "$id" | wc -l)

            if ((jobs_running == 1)); then
                break
            fi

            sleep 60
        done
    done

    echo "All jobs on r630 have been completed."
fi
