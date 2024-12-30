#!/usr/bin/env python3


import os
import subprocess
from time import sleep


def frange(start, stop, step):
    while start <= stop:
        yield round(start, 2)
        start += step


def run_command(command, error_message):
    try:
        return subprocess.check_output(command, shell=True, universal_newlines=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e.output}")
        return None


def change_directory(path):
    current_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(current_dir)


def generate_and_submit_jobs(molecules, a1, b1, a2, b2, co, ov, cv, mrmu, mu, geom_file="geometries.txt", max_jobs=10):
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_co_{co}_ov_{ov}_cv_{cv}_mrmu_{mrmu}_mu_{mu}'
    os.makedirs(state_dir, exist_ok=True)

    job_ids = []
    job_count = 0

    for molecule in molecules:
        inp_file = os.path.join(state_dir, f"{molecule}_{state_dir}.inp")
        print(f"Generating input file: {inp_file}")

        geom_data = run_command(f'./gen_geo.sh {molecule} {geom_file}', f"Error running gen_geo.sh for {molecule}")
        if not geom_data:
            print(f"[ERROR] Geometry data for {molecule} is empty or invalid.")
            continue

        try:
            with open(inp_file, 'w') as f:
                f.write(f""" $CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0
 TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 $END
 $TDDFT NSTATE=50 IROOT=1 MULT=1 mralp={a2} mrbet={b2} $END
 $TDDFT spcp(1)={co},{ov},{cv} mrmu={mrmu} tammd=.t. $END
 $DFT alphac={a1} betac={b1} mu={mu} $END
 $SCF DIRSCF=.t. diis=.f. damp=.t.
  soscf=.t. shift=.t. couple=.t.
  alpha(1)=0.5,0.5,0.5 beta(1)=0.5,0.5,0.5 $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $SYSTEM TIMLIM=999999100 MWORDS=500 kdiag=1 $END
 $DATA
 {molecule}
 C1
""")
                f.write(geom_data)
                f.write(" $END\n")
            print(f"[INFO] Successfully generated input file for {molecule}")
        except Exception as ex:
            print(f"[ERROR] Failed to generate input file for {molecule}: {ex}")
            continue

        try:
            print(f"[INFO] Submitting job for {molecule}...")
            job_submission_command = f"gms_sbatch -p trd -n 30 -i {molecule}_{state_dir}.inp"
            with change_directory(state_dir):
                job_id = run_command(job_submission_command, f"Error submitting job for {molecule}")
                if job_id:
                    job_ids.append(job_id)
                    print(f"[INFO] Job submitted with ID: {job_id}")
                    job_count += 1

            if job_count >= max_jobs:
                print(f"[INFO] Reached max job limit of {max_jobs}. Waiting for jobs to complete...")
                wait_for_all_jobs_to_complete(job_ids)
                job_count = 0
                job_ids = []

        except Exception as e:
            print(f"[ERROR] Error during job submission for {molecule}: {e}")

    if job_ids:
        print("[INFO] Waiting for remaining jobs to complete...")
        wait_for_all_jobs_to_complete(job_ids)

    print("[INFO] All jobs submitted and completed.")
    return job_ids


def wait_for_all_jobs_to_complete(job_ids, timeout=3600):
    elapsed_time = 0
    while job_ids and elapsed_time < timeout:
        for job_id in list(job_ids):
            print(f"[INFO] Waiting for job {job_id} to complete...")
            result = run_command(f"squeue -j {job_id}", f"[ERROR] Error checking status for job {job_id}")
            if result and job_id not in result:
                print(f"[INFO] Job {job_id} has completed.")
                job_ids.remove(job_id)
            else:
                print(f"[INFO] Job {job_id} is still running. Waiting...")
        sleep(30)
        elapsed_time += 30
    if job_ids:
        print("[WARNING] Timeout reached! Remaining unfinished jobs:", job_ids)


a1_values = [round(x, 2) for x in frange(0.40, 0.75, 0.01)]
b1_values = [round(x, 2) for x in frange(-0.35, -0.15, 0.01)]
a2_values = [round(x, 2) for x in frange(0.40, 0.75, 0.01)]
b2_values = [round(x, 2) for x in frange(-0.30, -0.05, 0.01)]
co_values = [round(x, 2) for x in frange(0.40, 0.75, 0.01)]
ov_values = [round(x, 2) for x in frange(0.40, 0.75, 0.01)]
cv_values = [round(x, 2) for x in frange(0.40, 0.75, 0.01)]
mrmu_values = [round(x, 2) for x in frange(0.25, 0.40, 0.01)]
mu_values = [round(x, 2) for x in frange(0.25, 0.40, 0.01)]

molecules = ["Ethene", "E-Butadiene"]
max_jobs = 50

