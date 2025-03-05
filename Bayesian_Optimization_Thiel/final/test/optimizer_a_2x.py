#!/usr/bin/env python3

import os
import re
import csv
import math
import subprocess
from time import sleep
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
import glob

# --- Parameter Space Definition ---
space = {
    'a1': hp.uniform('a1', -1.00, 1.00),
    'b1': hp.uniform('b1', -1.00, 1.00),
    'a2': hp.uniform('a2', -1.00, 1.00),
    'b2': hp.uniform('b2', -1.00, 1.00),
    'co': hp.uniform('co', 0.40, 0.75),
    'ov': hp.uniform('ov', 0.40, 0.75),
    'cv': hp.uniform('cv', 0.40, 0.75),
    'mrmu': hp.uniform('mrmu', 0.25, 0.40),
    'mu': hp.uniform('mu', 0.25, 0.40),
}

# --- Reference Data ---
VEE_ref = {
    "Ethene": [7.8],
    "E-Butadiene": [6.18, 6.55],
    "all-E-Hexatriene": [5.10, 5.09],
    "all-E-Octatetraene": [4.47, 4.66],
    "Cyclopropene": [6.67, 6.68],
    "Cyclopentadiene": [5.55, 6.28],
    "Norbornadiene": [5.37, 6.28],
    "Benzene": [5.08, 6.54, 7.13, 8.15],
    "Naphthalene": [4.25, 4.82, 5.90, 5.75, 6.11, 6.46, 6.36, 6.49],
    "Furan": [6.32, 6.57, 8.13],
    "Pyrrole": [6.37, 6.57, 7.91],
    "Imidazole": [6.65, 6.25, 6.73],
    "Pyridine": [4.85, 4.59, 5.11, 6.26, 7.18, 7.27],
    "Pyrazine": [4.13, 4.98, 4.97, 5.65, 6.69, 6.83, 7.86, 7.81],
    "Pyrimidine": [4.43, 4.85, 5.34, 6.82],
    "Pyridazine": [3.85, 4.55, 5.20, 5.66],
    "s-Triazine": [4.70, 4.71, 4.75, 5.71],
    "s-Tetrazine": [2.46, 3.78, 4.87, 5.08, 5.28, 5.76, 5.39],
    "Formaldehyde": [3.88, 9.04, 9.29],
    "Acetone": [4.38, 9.04, 8.90],
    "p-Benzoquinone": [2.86, 2.74, 4.44, 5.47, 5.55, 7.16],
    "Formamide": [5.55, 7.35],
    "Acetamide": [5.62, 7.14],
    "Propanamide": [5.65, 7.09],
    "Cytosine": [4.66, 4.87, 5.26, 5.62],
    "Thymine": [4.82, 5.20, 6.27, 6.16, 6.53],
    "Uracil": [4.80, 5.35, 6.26, 6.10, 6.56, 6.70],
    "Adenine": [5.25, 5.25, 5.12, 5.75]
}

# --- Molecule List & Job Limit ---
molecules = ["Ethene", "E-Butadiene", "all-E-Hexatriene", "all-E-Octatetraene",
             "Cyclopropene", "Cyclopentadiene", "Norbornadiene", "Benzene",
             "Naphthalene", "Furan", "Pyrrole", "Imidazole", "Pyridine",
             "Pyrazine", "Pyrimidine", "Pyridazine", "s-Triazine", "s-Tetrazine",
             "Formaldehyde", "Acetone", "p-Benzoquinone", "Formamide", "Acetamide",
             "Propanamide", "Cytosine", "Thymine", "Uracil", "Adenine"]

max_jobs = 56  # Target concurrent jobs

# --- Utility Functions ---
def frange(start, stop, step):
    while start <= stop:
        yield round(start, 2)
        start += step

def run_command(command, error_message):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True).strip()
        return output
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e.output if hasattr(e, 'output') else str(e)}")
        return None

class DirectoryContext:
    def __init__(self, path):
        self.path = path
        self.original_dir = os.getcwd()
    def __enter__(self):
        os.chdir(self.path)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_dir)

# --- Job Management Functions ---
def extract_job_id(job_output):
    if not job_output:
        return None
    match = re.search(r'Submitted batch job (\d+)', job_output)
    if match:
        return match.group(1)
    return job_output

def check_job_status(job_id):
    try:
        result = subprocess.check_output(f"squeue -j {job_id}", shell=True, universal_newlines=True).strip()
        return job_id in result
    except subprocess.CalledProcessError:
        return False

def wait_for_jobs_to_finish(job_ids, check_interval=1, timeout=3600):
    remaining_jobs = job_ids.copy()
    elapsed_time = 0
    while remaining_jobs and elapsed_time < timeout:
        print(f"Waiting for {len(remaining_jobs)} jobs to complete...")
        for job_id in list(remaining_jobs):
            if not check_job_status(job_id):
                print(f"Job {job_id} has completed.")
                remaining_jobs.remove(job_id)
        if remaining_jobs:
            sleep(check_interval)
            elapsed_time += check_interval
    if remaining_jobs:
        print(f"Warning: Timeout reached with {len(remaining_jobs)} jobs still running")
    else:
        print("All jobs have completed successfully.")
    return [job_id for job_id in job_ids if job_id not in remaining_jobs]

# --- Data Extraction Functions ---
def manage_job_queue(molecules, params, geom_file="geometries.txt", target_concurrent_jobs=56):
    """
    Generate input files and submit jobs while trying to keep up to target_concurrent_jobs running.
    Each molecule is processed only once per parameter set.
    """
    a1, b1, a2, b2, co, ov, cv, mrmu, mu = (
        params['a1'], params['b1'], params['a2'], params['b2'],
        params['co'], params['ov'], params['cv'], params['mrmu'], params['mu']
    )
    
    # Unique state directory based on current parameter set
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_co_{co}_ov_{ov}_cv_{cv}_mrmu_{mrmu}_mu_{mu}'
    os.makedirs(state_dir, exist_ok=True)

    all_job_ids = []
    active_job_ids = []
    job_mapping = {}  # Maps job_id -> molecule

    # Build the job queue: one run per molecule (no duplication)
    job_queue = list(molecules)  # Each molecule runs once

    # Initial submission: submit all available jobs (up to the number of molecules)
    while len(active_job_ids) < target_concurrent_jobs and job_queue:
        molecule = job_queue.pop(0)
        inp_file = os.path.join(state_dir, f"{molecule}_{state_dir}.inp")
        print(f"Generating input file: {inp_file}")
        geom_data = run_command(f'./gen_geo.sh {molecule} {geom_file}', 
                                f"Error getting geometry for {molecule}")
        if not geom_data:
            print(f"ERROR: Geometry data for {molecule} is empty or invalid.")
            continue
        try:
            with open(inp_file, 'w') as f:
                f.write(f""" $CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0
 TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 $END
 $TDDFT NSTATE=50 IROOT=1 MULT=1 mralp={a2} mrbet={b2} $END
 $TDDFT spcp(1)={co},{ov},{cv} mrmu={mrmu} tammd=.t. $END
 $DFT alphac={a1} betac={b1} mu={mu} $END
 $SCF DIRSCF=.t. diis=.t. damp=.t.
  soscf=.f. shift=.t. couple=.t.
  alpha(1)=0.5,0.5,0.5 beta(1)=0.5,0.5,0.5 $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $SYSTEM TIMLIM=999999100 MWORDS=500 kdiag=1 $END
 $DATA
 {molecule}
""")
                f.write(geom_data)
                f.write(" \n$END\n")
        except Exception as e:
            print(f"ERROR: Failed to create input file for {molecule}: {e}")
            continue

        try:
            with DirectoryContext(state_dir):
                job_submission_command = f"gms_sbatch -p ryzn,r630,r640 -c 28 -i {molecule}_{state_dir}.inp"
                job_output = run_command(job_submission_command, f"Error submitting job for {molecule}")
                if job_output:
                    job_id = extract_job_id(job_output)
                    if job_id:
                        print(f"Job submitted for {molecule} with ID: {job_id}")
                        all_job_ids.append(job_id)
                        active_job_ids.append(job_id)
                        job_mapping[job_id] = molecule
                    else:
                        print(f"ERROR: Failed to extract job ID from output: {job_output}")
                else:
                    print(f"ERROR: Failed to get job submission output for {molecule}")
        except Exception as e:
            print(f"ERROR: Exception during job submission for {molecule}: {e}")
            continue

    # Continuous monitoring until all jobs are completed
    while active_job_ids or job_queue:
        # Remove finished jobs from active list
        for job_id in active_job_ids.copy():
            if not check_job_status(job_id):
                print(f"Job {job_id} for molecule {job_mapping.get(job_id, 'unknown')} has completed.")
                active_job_ids.remove(job_id)
        # Submit new jobs if any remain in the queue
        while len(active_job_ids) < target_concurrent_jobs and job_queue:
            molecule = job_queue.pop(0)
            inp_file = os.path.join(state_dir, f"{molecule}_{state_dir}.inp")
            print(f"Generating input file: {inp_file}")
            geom_data = run_command(f'./gen_geo.sh {molecule} {geom_file}', 
                                    f"Error getting geometry for {molecule}")
            if not geom_data:
                print(f"ERROR: Geometry data for {molecule} is empty or invalid.")
                continue
            try:
                with open(inp_file, 'w') as f:
                    f.write(f""" $CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0
 TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 $END
 $TDDFT NSTATE=50 IROOT=1 MULT=1 mralp={a2} mrbet={b2} $END
 $TDDFT spcp(1)={co},{ov},{cv} mrmu={mrmu} tammd=.t. $END
 $DFT alphac={a1} betac={b1} mu={mu} $END
 $SCF DIRSCF=.t. diis=.t. damp=.t.
  soscf=.f. shift=.t. couple=.t.
  alpha(1)=0.5,0.5,0.5 beta(1)=0.5,0.5,0.5 $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $SYSTEM TIMLIM=999999100 MWORDS=500 kdiag=1 $END
 $DATA
 {molecule}
""")
                    f.write(geom_data)
                    f.write(" \n$END\n")
            except Exception as e:
                print(f"ERROR: Failed to create input file for {molecule}: {e}")
                continue
            try:
                with DirectoryContext(state_dir):
                    job_submission_command = f"gms_sbatch -p ryzn,r630,r640 -c 28 -i {molecule}_{state_dir}.inp"
                    job_output = run_command(job_submission_command, f"Error submitting job for {molecule}")
                    if job_output:
                        job_id = extract_job_id(job_output)
                        if job_id:
                            print(f"Job submitted for {molecule} with ID: {job_id}")
                            all_job_ids.append(job_id)
                            active_job_ids.append(job_id)
                            job_mapping[job_id] = molecule
                        else:
                            print(f"ERROR: Failed to extract job ID from output: {job_output}")
                    else:
                        print(f"ERROR: Failed to get job submission output for {molecule}")
            except Exception as e:
                print(f"ERROR: Exception during job submission for {molecule}: {e}")
                continue
        print(f"Current status: {len(active_job_ids)} active jobs, {len(job_queue)} jobs in queue.")
        sleep(1)  # Poll every second
    print("All jobs have been submitted and completed.")
    return all_job_ids, job_mapping





def extract_log_data(molecules, params, job_mapping):
    # Aggregate results from potentially duplicate runs by averaging.
    a1, b1, a2, b2, co, ov, cv, mrmu, mu = (
        params['a1'], params['b1'], params['a2'], params['b2'],
        params['co'], params['ov'], params['cv'], params['mrmu'], params['mu']
    )
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_co_{co}_ov_{ov}_cv_{cv}_mrmu_{mrmu}_mu_{mu}'
    results = {}  # molecule -> list of VEE value lists

    for job_id, (molecule, run_idx) in job_mapping.items():
        vee_log = os.path.join(state_dir, f"{molecule}_{run_idx}_{state_dir}.log")
        print(f"Processing log for {molecule} (run {run_idx}): {vee_log}")
        retry_count = 0
        extracted_values = None
        while retry_count < 2:
            try:
                if not os.path.exists(vee_log):
                    raise FileNotFoundError(f"Log file not found: {vee_log}")
                if os.path.getsize(vee_log) == 0:
                    raise ValueError(f"Log file for {molecule} (run {run_idx}) is empty")
                with open(vee_log, 'r') as log:
                    content = log.read()
                    job_completed = ("CPU timing information for all processes" in content or 
                                     "ddikick.x: exited gracefully." in content)
                if not job_completed:
                    raise ValueError(f"Job for {molecule} (run {run_idx}) is not completed yet.")
                command = f"./3_read.sh {molecule} {vee_log}"
                result = run_command(command, f"Error processing {molecule} log file")
                print(f"AWK Output: {result}")
                if not result:
                    raise ValueError(f"No output from processing {molecule} log file")
                if "has problem" in result:
                    raise ValueError(f"SCF convergence issue detected for {molecule}")
                values = []
                for line in result.splitlines():
                    parts = line.split()
                    if len(parts) == 2:
                        try:
                            values.append(float(parts[1]))
                        except ValueError:
                            print(f"WARNING: Could not convert value for {molecule}")
                if not values:
                    raise ValueError(f"No valid VEE values found for {molecule}")
                extracted_values = values
                print(f"Extracted VEE for {molecule} (run {run_idx}): {values}")
                break
            except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"ERROR: {e}")
                retry_count += 1
                if retry_count < 2:
                    print(f"Retrying job for {molecule} (run {run_idx})...")
                    with DirectoryContext(state_dir):
                        job_submission_command = f"gms_sbatch -p chc4,xeon,trpro,r630,r640,ryzn -c 28 -i {molecule}_{run_idx}_{state_dir}.inp"
                        job_output = run_command(job_submission_command, f"Error resubmitting job for {molecule}")
                        if job_output:
                            new_job_id = extract_job_id(job_output)
                            if new_job_id:
                                print(f"Job resubmitted with ID: {new_job_id}")
                                wait_for_jobs_to_finish([new_job_id], check_interval=1)
                        else:
                            print("ERROR: Failed to get job submission output")
                else:
                    print(f"Skipping {molecule} (run {run_idx}) after failed retries.")
        if extracted_values:
            results.setdefault(molecule, []).append(extracted_values)
    # Aggregate by averaging duplicate runs per molecule.
    aggregated_data = []
    for molecule, value_lists in results.items():
        num_values = len(value_lists[0])
        avg_values = []
        for i in range(num_values):
            avg = sum(v[i] for v in value_lists) / len(value_lists)
            avg_values.append(avg)
        data_entry = {"molecule": molecule}
        for idx, vee in enumerate(avg_values):
            data_entry[f"VEE_{idx+1}"] = vee
        aggregated_data.append(data_entry)
        print(f"Aggregated VEE for {molecule}: {avg_values}")
    return aggregated_data

# --- Data Analysis Functions ---
def compare_with_reference(extracted_data, reference_data):
    comparison = []
    valid_differences = []
    skipped_molecules = []
    for entry in extracted_data:
        molecule = entry['molecule']
        try:
            vees = [float(entry[key]) for key in entry if key.startswith('VEE_')]
            ref_values = reference_data.get(molecule, [])
            if not ref_values:
                print(f"WARNING: No reference values found for {molecule}")
                skipped_molecules.append(molecule)
                continue
            for idx, vee in enumerate(vees):
                if idx < len(ref_values):
                    ref_vee = ref_values[idx]
                    vee_diff = vee - ref_vee
                    comparison.append({
                        'molecule': molecule,
                        f'VEE_{idx+1}_calculated': vee,
                        f'VEE_{idx+1}_reference': ref_vee,
                        f'VEE_{idx+1}_diff': vee_diff
                    })
                    valid_differences.append(abs(vee_diff))
                else:
                    print(f"WARNING: Extra VEE value for {molecule}: {vee}")
        except ValueError as e:
            print(f"ERROR: Could not convert VEE values for {molecule}: {e}")
            skipped_molecules.append(molecule)
            continue
    print(f"INFO: Skipped {len(skipped_molecules)} molecules due to errors.")
    return comparison, valid_differences

def calculate_rmse_mae(differences):
    if not differences:
        print("No valid differences for RMSE/MAE calculation.")
        return None, None
    mse = sum(diff ** 2 for diff in differences) / len(differences)
    rmse = math.sqrt(mse)
    mae = sum(differences) / len(differences)
    return rmse, mae

# --- Results Saving Functions ---
def save_extracted_data_to_csv(extracted_data, filename='extracted_data.csv'):
    if not extracted_data:
        print("WARNING: No data to save!")
        return
    all_keys = set()
    for row in extracted_data:
        all_keys.update(row.keys())
    fieldnames = sorted(list(all_keys))
    try:
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            dict_writer.writeheader()
            dict_writer.writerows(extracted_data)
        print(f"INFO: Data saved to {filename}")
    except Exception as e:
        print(f"ERROR: Failed to save data to {filename}: {e}")

def save_comparison_results_to_csv(comparison_data, filename='comparison_results.csv'):
    if not comparison_data:
        print("No comparison data to save.")
        return
    keys = comparison_data[0].keys() if comparison_data else []
    try:
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(comparison_data)
        print(f"Comparison data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")

def save_results_summary(params, rmse, mae, comparison_results, filename='results_summary.txt'):
    with open(filename, 'a') as f:
        f.write(
            f"Combination: a1={params['a1']:.2f}, b1={params['b1']:.2f}, a2={params['a2']:.2f}, "
            f"b2={params['b2']:.2f}, co={params['co']:.2f}, ov={params['ov']:.2f}, "
            f"cv={params['cv']:.2f}, mrmu={params['mrmu']:.2f}, mu={params['mu']:.2f}\n"
        )
        f.write(f"RMSE: {rmse:.4f}, MAE: {mae:.4f}\n")
        f.write("Per-molecule differences:\n")
        for result in comparison_results:
            molecule = result.get('molecule', 'Unknown')
            vee_diffs = [f"{k}={v:.4f}" for k, v in result.items() if k.startswith('VEE_') and k.endswith('_diff')]
            if vee_diffs:
                f.write(f"{molecule}: {', '.join(vee_diffs)}\n")
            else:
                f.write(f"{molecule}: No VEE differences found\n")
        f.write("\n")

# --- Optimization Functions ---
def round_params(params):
    return {k: round(v, 2) for k, v in params.items()}

def objective(params):
    params = round_params(params)
    print(f"Evaluating parameter set: {params}")
    job_ids, job_mapping = manage_job_queue(molecules, params, target_concurrent_jobs=max_jobs)
    extracted_data = extract_log_data(molecules, params, job_mapping)
    save_extracted_data_to_csv(extracted_data)
    comparison_results, valid_differences = compare_with_reference(extracted_data, VEE_ref)
    save_comparison_results_to_csv(comparison_results)
    rmse, mae = calculate_rmse_mae(valid_differences)
    if rmse is not None and mae is not None:
        print(f"RMSE: {rmse:.4f}, MAE: {mae:.4f}")
        save_results_summary(params, rmse, mae, comparison_results)
        return {'loss': rmse, 'status': STATUS_OK, 'mae': mae}
    else:
        print("Skipping combination due to invalid VEE differences.")
        return {'loss': float('inf'), 'status': STATUS_OK}

def main(max_evals=10):
    trials = Trials()
    best = fmin(
        fn=objective,
        space=space,
        algo=tpe.suggest,
        max_evals=max_evals,
        trials=trials
    )
    best_params = round_params({k: v for k, v in best.items()})
    print("\nOptimization completed.")
    print(f"Best parameters found: {best_params}")
    best_trial_idx = trials.best_trial['tid']
    best_loss = trials.results[best_trial_idx]['loss']
    best_mae = trials.results[best_trial_idx].get('mae', 'N/A')
    print(f"Best RMSE: {best_loss:.4f}")
    print(f"Best MAE: {best_mae}")
    with open('best_params.txt', 'w') as f:
        f.write("Best parameters found:\n")
        for k, v in best_params.items():
            f.write(f"{k} = {v:.2f}\n")
        f.write(f"Best RMSE: {best_loss:.4f}\n")
        f.write(f"Best MAE: {best_mae}\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run Bayesian optimization for VEE functional parameters.')
    parser.add_argument('--max-evals', type=int, default=2500, help='Maximum number of evaluations')
    parser.add_argument('--molecules', nargs='+', default=[
        "Ethene","E-Butadiene","all-E-Hexatriene","all-E-Octatetraene","Cyclopropene",
        "Cyclopentadiene","Norbornadiene","Benzene","Naphthalene","Furan",
        "Pyrrole","Imidazole","Pyridine","Pyrazine","Pyrimidine","Pyridazine",
        "s-Triazine","s-Tetrazine","Formaldehyde","Acetone","p-Benzoquinone",
        "Formamide","Acetamide","Propanamide","Cytosine","Thymine","Uracil","Adenine"
    ], help='List of molecules to optimize parameters for')
    parser.add_argument('--max-jobs', type=int, default=56, help='Maximum number of concurrent jobs')
    args = parser.parse_args()
    molecules = args.molecules
    max_jobs = args.max_jobs
    main(max_evals=args.max_evals)

