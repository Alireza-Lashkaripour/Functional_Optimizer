#!/bin/bash

# Function to generate input files in the given directory with the specified parameters
generate_input_files() {
    local dir=$1
    local a1=$2
    local b1=$3
    local a2=$4
    local b2=$5
    local state=$6
    local mult

    if [ "$state" == "T" ]; then
        mult=3
    else
        mult=1
    fi

    mkdir -p "$dir"
    cd "$dir" || exit

    for iii in Heptazine Cyclazine Molecule3 Molecule4 Molecule5 Molecule6 Molecule7 Molecule8 Molecule9 Molecule10; do
        inp="${iii}_${dir}"

        # Create the input file with the current parameters, ensuring each line starts with a space
        {
            echo " \$CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0"
            echo " TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 UNITS=BOHR \$END"
            echo " \$TDDFT NSTATE=3 IROOT=1 MULT=$mult mralp=$a2 mrbet=$b2 \$END"
            echo " \$TDDFT spcp(1)=0.5,0.5,0.5 \$END"
            echo " \$DFT alphac=$a1 betac=$b1 \$END"
            echo " \$SCF DIRSCF=.t. diis=.f. damp=.t."
            echo "  soscf=.f. shift=.t. FDIFF=.t. \$END"
            echo " \$BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 \$END"
            echo " \$SYSTEM TIMLIM=999999100 MWORDS=500 kdiag=1 \$END"
            echo " \$DATA"
            echo " $iii"
            echo " C1"
            "../gen_geo.sh" "$iii" "../../GW_binding_energy_geom.txt"
            echo " \$END"
        } > "$inp.inp"

        # Submit the job to r630 partition and capture the job ID
        job_id=$(gms_sbatch --job-name="${iii}_${a1}_${b1}_${a2}_${b2}_r630" -p r630,trd,ryzn -c 30 -i "$inp.inp" | awk '{print $4}')
        job_ids+=("$job_id")
        ((job_count++))

        # Check if we've reached the max jobs limit for the r630 partition
        if [ "$job_count" -ge "$max_jobs" ]; then
            echo "Max job count reached on r630. Waiting for all jobs to finish before submitting more..."

            for id in "${job_ids[@]}"; do
                while :; do
                    jobs_running=$(squeue -u "$USER" -p r630,trd,ryzn -j "$id" | wc -l)
                    if [ "$jobs_running" -le 1 ]; then
                        break
                    fi
                    sleep 10
                done
            done

            # Reset job counter and job IDs list for the next batch
            job_count=0
            job_ids=()
            echo "Batch of jobs completed on r630. Proceeding to the next batch..."
        fi
    done

    cd ..
}

# Initialize job counters and limits
job_count=0
max_jobs=100
job_ids=()

# Iterate over all _S and _T directories
for dir in *_S *_T; do
    if [[ "$dir" == *_S ]]; then
        # Extract the corresponding _T directory name
        corresponding_dir="${dir/_S/_T}"
        if [ ! -d "$corresponding_dir" ]; then
            # Missing _T folder, extract parameters and create it
            echo "Missing corresponding _T folder for $dir"
            params=(${dir//_/ })
            a1="${params[1]}"
            b1="${params[3]}"
            a2="${params[5]}"
            b2="${params[7]}"
            generate_input_files "$corresponding_dir" "$a1" "$b1" "$a2" "$b2" "T"
        fi
    elif [[ "$dir" == *_T ]]; then
        # Extract the corresponding _S directory name
        corresponding_dir="${dir/_T/_S}"
        if [ ! -d "$corresponding_dir" ]; then
            # Missing _S folder, extract parameters and create it
            echo "Missing corresponding _S folder for $dir"
            params=(${dir//_/ })
            a1="${params[1]}"
            b1="${params[3]}"
            a2="${params[5]}"
            b2="${params[7]}"
            generate_input_files "$corresponding_dir" "$a1" "$b1" "$a2" "$b2" "S"
        fi
    fi
done

# Final wait for any remaining jobs specifically on r630 if the last batch was not exactly $max_jobs
if [ "$job_count" -gt 0 ]; then
    echo "Final batch on r630. Waiting for remaining jobs to complete..."
    for id in "${job_ids[@]}"; do
        while :; do
            jobs_running=$(squeue -u "$USER" -p r630,trd,ryzn -j "$id" | wc -l)
            if [ "$jobs_running" -le 1 ]; then
                break
            fi
            sleep 10
        done
    done
    echo "All jobs on r630 have been completed."
fi

echo "Script completed. All missing folders have been created."

