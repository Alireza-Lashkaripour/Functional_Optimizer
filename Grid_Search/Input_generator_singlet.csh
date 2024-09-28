#!/bin/csh

# Define the ranges for a1, b1, a2, and b2

set a1_values = `seq 0.48 0.01 0.52`
set b1_values = `seq -0.18 -0.01 -0.28`
set a2_values = `seq 0.65 0.01 0.75`
set b2_values = `seq -0.12 0.01 -0.08`



# Job counter
set job_count = 0
# Maximum number of concurrent jobs
set max_jobs = 70
set job_ids = ()

# Loop over a1 values
foreach a1 ($a1_values)
    # Loop over b1 values
    foreach b1 ($b1_values)
        # Loop over a2 values
        foreach a2 ($a2_values)
            # Loop over b2 values
            foreach b2 ($b2_values)
                # Construct the directory name using the current a1, b1, a2, and b2 values
                set name = "a1_${a1}_b1_${b1}_a2_${a2}_b2_${b2}_S"
                mkdir -p ${name}
                cd ${name}

                # Loop over your molecules
                foreach iii (Heptazine Cyclazine Molecule3 Molecule4 Molecule5 Molecule6 Molecule7 Molecule8 Molecule9 Molecule10)
                    set inp="${iii}_${name}"
                    
                    # Create the input file with the current parameters
                    echo "" \$CONTRL " SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0" > $inp.inp
                    echo " TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 UNITS=BOHR " \$END >> $inp.inp
                    echo "" \$TDDFT " NSTATE=3 IROOT=1 MULT=1 mralp=$a2 mrbet=$b2 "  \$END >> $inp.inp
                    echo "" \$TDDFT " spcp(1)=0.5,0.5,0.5 "  \$END >> $inp.inp
                    echo "" \$DFT " alphac=$a1 betac=$b1 " \$END >> $inp.inp
                    echo "" \$SCF " DIRSCF=.t. diis=.f. damp=.t. "  >> $inp.inp
                    echo " soscf=.f. shift=.t. FDIFF=.t. " \$END >> $inp.inp
                    echo "" \$BASIS " GBASIS=N31 NGAUSS=6 NDFUNC=1 " \$END >> $inp.inp
                    echo "" \$SYSTEM " TIMLIM=999999100 MWORDS=500 kdiag=1 " \$END >> $inp.inp
                    echo "" \$DATA >> $inp.inp
                    echo " $iii " >> $inp.inp
                    echo " C1" >> $inp.inp
                    ../gen_geo.sh $iii ../../GW_binding_energy_geom.txt >> $inp.inp
                    echo " "\$END >> $inp.inp
                    
                    # Submit the job to r630 partition and capture the job ID
                    set job_id = `gms_sbatch --job-name="${iii}_${a1}_${b1}_${a2}_${b2}_r630" -p r630,trd,ryzn -c 30 -i $inp.inp | awk '{print $4}'`
                    set job_ids = ($job_ids $job_id)
                    @ job_count++

                    # Check if we've reached the max jobs limit for the r630 partition
                    if ($job_count == $max_jobs) then
                        echo "Max job count reached on r630. Waiting for all jobs to finish before submitting more..."
                        
                        foreach id ($job_ids)
                            while (1)
                                # Check specifically for jobs in the r630 partition
                                set jobs_running = `squeue -u $USER -p r630,trd,ryzn -j $id | wc -l`
                                if ($jobs_running == 1) break # Assumes job is no longer in the queue
                                sleep 10
                            end
                        end
                        
                        # Reset job counter and job IDs list for the next batch
                        set job_count = 0
                        set job_ids = ()
                        echo "Batch of jobs completed on r630. Proceeding to the next batch..."
                    endif
                end

                cd ..
            end
        end
    end
end

# Implement a final wait for any remaining jobs specifically on r630 if the last batch was not exactly $max_jobs
if ($job_count > 0) then
    echo "Final batch on r630. Waiting for remaining jobs to complete..."
    foreach id ($job_ids)
        while (1)
            set jobs_running = `squeue -u $USER -p r630,trd,ryzn -j $id | wc -l`
            if ($jobs_running == 1) break
            sleep 10
        end
    end
    echo "All jobs on r630 have been completed."
endif

