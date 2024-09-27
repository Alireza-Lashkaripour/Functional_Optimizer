#!/bin/bash

get_job_name() {
    job_name=$(basename "$1" | sed 's/\.log$//')
    echo "$job_name"
}

max_jobs=1000

job_count=0

job_ids=()

grep -r -l "Error changing to scratch directory" | xargs grep -H -m 1 "Error changing to scratch directory" | cut -d ":" -f 1 | sort -u |
while IFS= read -r log_file; do
    job_name=$(get_job_name "$log_file")

    job_folder=$(dirname "$log_file")
    cd "$job_folder" || { echo "Failed to change directory to $job_folder. Skipping..."; continue; }

    input_file="$job_name.inp"
    if [ -e "$input_file" ]; then
        job_id=$(gms_sbatch -p trd -i "$input_file" | awk '{print $4}')
        job_ids+=("$job_id")

        ((job_count++))

        if ((job_count == max_jobs)); then
            echo "Max job count reached on trd. Waiting for all jobs to finish before submitting more..."

            for id in "${job_ids[@]}"; do
                while true; do
                    jobs_running=$(squeue -u "$USER" -p trd -j "$id" | wc -l)

                    if ((jobs_running == 1)); then
                        break
                    fi

                    sleep 60
                done
            done

            job_count=0
            job_ids=()
            echo "Batch of jobs completed on trd. Proceeding to the next batch..."
        fi

        echo "Rerunning job for $log_file"
    else
        echo "Input file not found for $log_file. Skipping..."
    fi

    cd - > /dev/null
done

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
