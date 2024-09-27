#!/usr/bin/env python3

import os
import subprocess
from time import sleep

def frange(start, stop, step):
    while start < stop:
        yield round(start, 2)
        start += step

def generate_input_files_and_submit(molecules, a1, b1, a2, b2, co, ov, cv, mu, state, geom_file="geometries.txt", max_jobs=10):
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_co_{co}_ov_{ov}_cv_{cv}_mu_{mu}_{state}'

    if not os.path.exists(state_dir):
        os.makedirs(state_dir)

    mult_tddft = '1' if state == 'S' else '3'

    job_ids = []  
    job_count = 0

    for molecule in molecules:
        inp_file = os.path.join(state_dir, f"{molecule}_{state_dir}.inp")
        print(f"Generating input file: {inp_file}")

        try:
            command = f'./gen_geo.sh {molecule} {geom_file}'
            geom_data = subprocess.check_output(command, shell=True).decode()

            with open(inp_file, 'w') as f:
                f.write(f""" $CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0
 TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 UNITS=BOHR $END
 $TDDFT NSTATE=3 IROOT=1 MULT={mult_tddft} mralp={a2} mrbet={b2} $END
 $TDDFT spcp(1)={co},{co},{co} mrmu={mu} $END
 $DFT alphac={a1} betac={b1} $END
 $SCF DIRSCF=.t. diis=.f. damp=.t.
  soscf=.f. shift=.t. FDIFF=.t. $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $SYSTEM TIMLIM=999999100 MWORDS=500 kdiag=1 $END
 $DATA
 {molecule}
 C1
""")
                f.write(geom_data)
                f.write(" $END\n")
            print(f"Successfully generated {inp_file}")

        except subprocess.CalledProcessError as e:
            print(f"Error running gen_geo.sh for {molecule}: {e}")
            print(f"Command output: {e.output.decode()}")
            continue

        except Exception as ex:
            print(f"Unexpected error: {ex}")
            continue

        try:
            print(f"Submitting job for {molecule}...")
            job_submission_command = f"gms_sbatch -p r630 -c 30 -i {molecule}_{state_dir}.inp"
            current_dir = os.getcwd()
            os.chdir(state_dir)  
            job_id = subprocess.check_output(job_submission_command, shell=True).strip().decode()
            os.chdir(current_dir)  

            job_ids.append(job_id)  
            print(f"Job submitted with ID: {job_id}")
            job_count += 1

            if job_count >= max_jobs:
                print(f"Reached max job limit of {max_jobs}. Waiting for jobs to complete...")
                wait_for_all_jobs_to_complete(job_ids)
                job_count = 0
                job_ids = []  #

        except subprocess.CalledProcessError as e:
            print(f"Error submitting job for {molecule}: {e}")
            print(f"Command output: {e.output.decode()}")
            os.chdir(current_dir)

    if job_ids:
        print(f"Waiting for remaining jobs to complete...")
        wait_for_all_jobs_to_complete(job_ids)

    print(f"All jobs submitted and completed.")
    return job_ids  

def wait_for_all_jobs_to_complete(job_ids):
    while job_ids:
        for job_id in list(job_ids):  
            print(f"Waiting for job {job_id} to complete...")
            try:
                job_status_command = f"squeue -j {job_id}"
                result = subprocess.run(job_status_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if job_id not in result.stdout.decode():
                    print(f"Job {job_id} has completed.")
                    job_ids.remove(job_id)  
                else:
                    print(f"Job {job_id} is still running. Waiting...")
            except Exception as e:
                print(f"Error checking status for job {job_id}: {e}")
        sleep(30)  

a1_values = [round(x, 2) for x in list(frange(0.45, 0.55, 0.01))]
b1_values = [round(x, 2) for x in list(frange(-0.28, -0.18, 0.01))]
a2_values = [round(x, 2) for x in list(frange(0.60, 0.75, 0.01))]
b2_values = [round(x, 2) for x in list(frange(-0.12, -0.08, 0.01))]
co_values = [round(x, 2) for x in list(frange(0.40, 0.75, 0.01))]
ov_values = [round(x, 2) for x in list(frange(0.40, 0.75, 0.01))]
cv_values = [round(x, 2) for x in list(frange(0.40, 0.75, 0.01))]
mu_values = [round(x, 2) for x in list(frange(0.25, 0.40, 0.01))]

molecules = ["Heptazine", "Cyclazine", "Molecule3", "Molecule4", "Molecule5",
             "Molecule6", "Molecule7", "Molecule8", "Molecule9", "Molecule10"]

max_jobs = 50  

