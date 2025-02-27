#!/usr/bin/env python3

import os
import subprocess
import csv
import math
from time import sleep
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials

# Configuration
MOLECULES = ["Ethene", "E-Butadiene"]
MAX_JOBS = 20
VEE_REF = {
    "Ethene": [7.8],
    "E-Butadiene": [6.18, 6.55]
}

# Hyperopt search space
SPACE = {
    'a1': hp.uniform('a1', 0.40, 0.75),
    'b1': hp.uniform('b1', -0.35, -0.15),
    'a2': hp.uniform('a2', 0.40, 0.75),
    'b2': hp.uniform('b2', -0.30, -0.05),
    'co': hp.uniform('co', 0.40, 0.75),
    'ov': hp.uniform('ov', 0.40, 0.75),
    'cv': hp.uniform('cv', 0.40, 0.75),
    'mrmu': hp.uniform('mrmu', 0.25, 0.40),
    'mu': hp.uniform('mu', 0.25, 0.40),
}

def run_command(command, error_message):
    try:
        return subprocess.check_output(command, shell=True, universal_newlines=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e.output}")
        return None

def wait_for_jobs(job_ids, timeout=3600):
    elapsed_time = 0
    while job_ids and elapsed_time < timeout:
        for job_id in list(job_ids):
            result = run_command(f"squeue -j {job_id}", f"Error checking status for job {job_id}")
            if result and job_id not in result:
                job_ids.remove(job_id)
                print(f"Job {job_id} completed")
            else:
                print(f"Job {job_id} still running")
        if job_ids:
            sleep(30)
            elapsed_time += 30
    return len(job_ids) == 0

def generate_input_file(molecule, params, state_dir, geom_file="geometries.txt"):
    inp_file = os.path.join(state_dir, f"{molecule}_{state_dir}.inp")
    geom_data = run_command(f'./gen_geo.sh {molecule} {geom_file}', 
                           f"Error getting geometry for {molecule}")
    
    if not geom_data:
        return None

    try:
        with open(inp_file, 'w') as f:
            f.write(f""" $CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0
 TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 $END
 $TDDFT NSTATE=50 IROOT=1 MULT=1 mralp={params['a2']} mrbet={params['b2']} $END
 $TDDFT spcp(1)={params['co']},{params['ov']},{params['cv']} mrmu={params['mrmu']} tammd=.t. $END
 $DFT alphac={params['a1']} betac={params['b1']} mu={params['mu']} $END
 $SCF DIRSCF=.t. diis=.f. damp=.t.
  soscf=.t. shift=.t. couple=.t.
  alpha(1)=0.5,0.5,0.5 beta(1)=0.5,0.5,0.5 $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $SYSTEM TIMLIM=999999100 MWORDS=500 kdiag=1 $END
 $DATA
{molecule}
{geom_data}
$END
""")
        return inp_file
    except Exception as e:
        print(f"Error generating input file for {molecule}: {e}")
        return None

def extract_vee_data(log_file, molecule):
    try:
        command = f"./3_read.sh {molecule} {log_file}"
        result = run_command(command, "Error extracting VEE data")
        if "has problem" in result:
            return None
        
        values = []
        for line in result.splitlines():
            parts = line.split()
            if len(parts) == 2:
                values.append(float(parts[1]))
        return values
    except Exception as e:
        print(f"Error extracting VEE data: {e}")
        return None

def calculate_metrics(calculated, reference):
    differences = []
    for calc, ref in zip(calculated, reference):
        differences.append(abs(calc - ref))
    
    if differences:
        mse = sum(d * d for d in differences) / len(differences)
        rmse = math.sqrt(mse)
        mae = sum(differences) / len(differences)
        return rmse, mae
    return None, None

def objective(params):
    # Round parameters to 2 decimal places
    params = {k: round(v, 2) for k, v in params.items()}
    
    state_dir = f'a1_{params["a1"]}_b1_{params["b1"]}_a2_{params["a2"]}_b2_{params["b2"]}_co_{params["co"]}_ov_{params["ov"]}_cv_{params["cv"]}_mrmu_{params["mrmu"]}_mu_{params["mu"]}'
    os.makedirs(state_dir, exist_ok=True)

    job_ids = []
    for molecule in MOLECULES:
        inp_file = generate_input_file(molecule, params, state_dir)
        if inp_file:
            job_id = run_command(f"gms_sbatch -p trd -n 30 -i {os.path.basename(inp_file)}", 
                               f"Error submitting job for {molecule}")
            if job_id:
                job_ids.append(job_id)

    if not wait_for_jobs(job_ids):
        return {'loss': float('inf'), 'status': STATUS_OK}

    all_differences = []
    for molecule in MOLECULES:
        log_file = os.path.join(state_dir, f"{molecule}_{state_dir}.log")
        vee_values = extract_vee_data(log_file, molecule)
        
        if vee_values and molecule in VEE_REF:
            ref_values = VEE_REF[molecule]
            for calc, ref in zip(vee_values, ref_values):
                all_differences.append(abs(calc - ref))

    if all_differences:
        rmse = math.sqrt(sum(d * d for d in all_differences) / len(all_differences))
        return {'loss': rmse, 'status': STATUS_OK}
    
    return {'loss': float('inf'), 'status': STATUS_OK}

def main():
    trials = Trials()
    best = fmin(
        fn=objective,
        space=SPACE,
        algo=tpe.suggest,
        max_evals=100,
        trials=trials
    )
    
    print("Best parameters found:", best)
    print("Best RMSE:", trials.best_trial['result']['loss'])

if __name__ == "__main__":
    main()
