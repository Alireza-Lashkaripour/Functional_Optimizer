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
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        print(f"[DEBUG] Command: {command}")
        print(f"[DEBUG] stdout: {stdout}")
        print(f"[DEBUG] stderr: {stderr}")
        if process.returncode != 0:
            print(f"[ERROR] Command failed with return code {process.returncode}")
            return None
        return stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e.output}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error running command: {str(e)}")
        return None

def change_directory(path):
    current_dir = os.getcwd()
    try:
        os.chdir(path)
        print(f"[DEBUG] Changed directory to: {path}")
        yield
    finally:
        os.chdir(current_dir)
        print(f"[DEBUG] Returned to directory: {current_dir}")

def generate_input_file(molecule, state_dir, a1, b1, a2, b2, co, ov, cv, mrmu, mu, geom_file="geometries.txt"):
    # Debug prints for file existence
    print(f"\n[DEBUG] Starting input file generation for {molecule}")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    print(f"[DEBUG] Checking for geometries.txt: {os.path.exists(geom_file)}")
    print(f"[DEBUG] Checking for gen_geo.sh: {os.path.exists('./gen_geo.sh')}")
    
    # Create full path for input file
    inp_file = os.path.join(state_dir, f"{molecule}_{state_dir}.inp")
    print(f"[INFO] Will generate input file: {inp_file}")
    
    # Make gen_geo.sh executable if it exists
    if os.path.exists('./gen_geo.sh'):
        try:
            os.chmod('./gen_geo.sh', 0o755)
            print("[DEBUG] Made gen_geo.sh executable")
        except Exception as e:
            print(f"[ERROR] Failed to make gen_geo.sh executable: {str(e)}")
            return None
    else:
        print("[ERROR] gen_geo.sh not found in current directory")
        return None
    
    # Get geometry data with more verbose output
    print(f"[INFO] Running gen_geo.sh for {molecule}")
    geom_command = f'./gen_geo.sh {molecule} {geom_file}'
    print(f"[DEBUG] Running command: {geom_command}")
    
    try:
        process = subprocess.Popen(geom_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        
        print(f"[DEBUG] Command stdout: {stdout}")
        print(f"[DEBUG] Command stderr: {stderr}")
        print(f"[DEBUG] Return code: {process.returncode}")
        
        if process.returncode != 0:
            print(f"[ERROR] gen_geo.sh failed with return code {process.returncode}")
            return None
            
        geom_data = stdout.strip()
        
        if not geom_data:
            print("[ERROR] No geometry data returned")
            return None
            
        print(f"[DEBUG] Geometry data received (first 50 chars): {geom_data[:50]}...")
        
    except Exception as e:
        print(f"[ERROR] Exception while running gen_geo.sh: {str(e)}")
        return None

    try:
        # Ensure directory exists
        os.makedirs(state_dir, exist_ok=True)
        print(f"[DEBUG] Created directory: {state_dir}")
        
        # Create input file content
        inp_content = f""" $CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0
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
{geom_data}
 $END
"""
        # Write input file
        with open(inp_file, 'w') as f:
            f.write(inp_content)
        
        print(f"[INFO] Successfully generated input file: {inp_file}")
        print(f"[DEBUG] Input file exists: {os.path.exists(inp_file)}")
        return inp_file
    
    except Exception as e:
        print(f"[ERROR] Failed to generate input file for {molecule}: {e}")
        return None

def generate_and_submit_jobs(molecules, a1, b1, a2, b2, co, ov, cv, mrmu, mu, geom_file="geometries.txt", max_jobs=10):
    print("\n[DEBUG] Starting new job generation with parameters:")
    print(f"a1={a1}, b1={b1}, a2={a2}, b2={b2}, co={co}, ov={ov}, cv={cv}, mrmu={mrmu}, mu={mu}")
    
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_co_{co}_ov_{ov}_cv_{cv}_mrmu_{mrmu}_mu_{mu}'
    print(f"[DEBUG] Working with state directory: {state_dir}")
    
    job_ids = []
    job_count = 0

    for molecule in molecules:
        print(f"\n[DEBUG] Processing molecule: {molecule}")
        
        # First, generate the input file
        inp_file = generate_input_file(molecule, state_dir, a1, b1, a2, b2, co, ov, cv, mrmu, mu, geom_file)
        
        if not inp_file:
            print(f"[ERROR] Failed to generate input file for {molecule}, skipping...")
            continue

        # Verify input file exists
        if not os.path.exists(inp_file):
            print(f"[ERROR] Input file {inp_file} was not created successfully")
            continue

        try:
            # Submit the job
            print(f"[INFO] Submitting job for {molecule}...")
            molecule_base = os.path.basename(inp_file).replace('.inp', '')
            job_submission_command = f"gms_sbatch -p trd -n 30 -i {molecule_base}"
            
            print(f"[DEBUG] Submitting with command: {job_submission_command}")
            print(f"[DEBUG] From directory: {state_dir}")
            
            with change_directory(state_dir):
                job_id = run_command(job_submission_command, f"Error submitting job for {molecule}")
                if job_id:
                    job_ids.append(job_id)
                    print(f"[INFO] Job submitted with ID: {job_id}")
                    job_count += 1
                else:
                    print(f"[ERROR] Failed to get job ID for {molecule}")

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

# Parameter ranges
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

if __name__ == "__main__":
    print("[DEBUG] Starting script execution")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    
    # Check for required files
    if not os.path.exists('./gen_geo.sh'):
        print("[ERROR] gen_geo.sh not found in current directory!")
        exit(1)
    
    if not os.path.exists('geometries.txt'):
        print("[ERROR] geometries.txt not found in current directory!")
        exit(1)
        
    print("[DEBUG] Required files found, proceeding with execution")
    
    # Make gen_geo.sh executable
    try:
        os.chmod('./gen_geo.sh', 0o755)
        print("[DEBUG] Made gen_geo.sh executable")
    except Exception as e:
        print(f"[ERROR] Failed to make gen_geo.sh executable: {str(e)}")
        exit(1)

    # Main loop with limited iterations for testing
    for a1 in a1_values[:1]:  # Test with first value only
        for b1 in b1_values[:1]:
            for a2 in a2_values[:1]:
                for b2 in b2_values[:1]:
                    for co in co_values[:1]:
                        for ov in ov_values[:1]:
                            for cv in cv_values[:1]:
                                for mrmu in mrmu_values[:1]:
                                    for mu in mu_values[:1]:
                                        print(f"\n[DEBUG] Testing combination: a1={a1}, b1={b1}, a2={a2}, b2={b2}, co={co}, ov={ov}, cv={cv}, mrmu={mrmu}, mu={mu}")
                                        generate_and_submit_jobs(
                                            molecules=molecules,
                                            a1=a1, b1=b1, a2=a2, b2=b2,
                                            co=co, ov=ov, cv=cv,
                                            mrmu=mrmu, mu=mu,
                                            max_jobs=max_jobs
                                        )
