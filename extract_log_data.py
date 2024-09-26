#!/usr/bin/env python3


import os
import re
import csv
import subprocess
from time import sleep
import math

def rerun_job(molecule, a1, b1, a2, b2, state):
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_{state}'
    inp_file = f"{molecule}_{state_dir}.inp"

    current_dir = os.getcwd()
    job_dir = os.path.join(current_dir, state_dir)

    if not os.path.exists(job_dir):
        print(f"Directory {job_dir} does not exist.")
        return None

    try:
        os.chdir(job_dir)  
        print(f"Rerunning job for {molecule} in directory {job_dir}...")
        job_submission_command = f"gms_sbatch -p r630 -c 30 -i {inp_file}"
        job_id = subprocess.check_output(job_submission_command, shell=True).strip().decode()
        print(f"Job resubmitted with ID: {job_id}")
        wait_for_specific_jobs_to_finish([job_id])
        os.chdir(current_dir)  
        return job_id
    except subprocess.CalledProcessError as e:
        print(f"Failed to resubmit job for {molecule}. Command output: {e.output.decode()}")
        os.chdir(current_dir)  
        return None
    except Exception as e:
        print(f"An error occurred while rerunning the job for {molecule}: {e}")
        os.chdir(current_dir)  
        return None

def wait_for_specific_jobs_to_finish(job_ids):
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

def ensure_job_completion(job_ids):
    print("Ensuring all jobs are finished before data extraction...")
    wait_for_specific_jobs_to_finish(job_ids)
    print("All jobs have completed.")

def check_job_completion(log_file):
    """Check for job completion by searching for specific phrases in the log."""
    if os.path.exists(log_file):
        with open(log_file, 'r') as log:
            content = log.read()
            if "CPU timing information for all processes" in content or "ddikick.x: exited gracefully." in content:
                return True
    return False

def extract_log_data(molecules, a1, b1, a2, b2, job_ids):
    ensure_job_completion(job_ids)

    singlet_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_S'
    triplet_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_T'

    data = []

    s0_pattern = re.compile(r"1\s+A\s+([-+]?\d*\.\d+|\d+)")  # Ground state energy
    s1_pattern = re.compile(r"2\s+A\s+([-+]?\d*\.\d+|\d+)")  # Singlet state energy
    t1_pattern = re.compile(r"1\s+A\s+([-+]?\d*\.\d+|\d+)")  # Triplet state energy

    for molecule in molecules:
        singlet_log = os.path.join(singlet_dir, f"{molecule}_{singlet_dir}.log")
        triplet_log = os.path.join(triplet_dir, f"{molecule}_{triplet_dir}.log")

        print(f"\nProcessing molecule: {molecule}")
        print(f"Singlet log path: {singlet_log}")
        print(f"Triplet log path: {triplet_log}")

        retry_count = 0
        while retry_count < 2:  
            try:
                if not check_job_completion(singlet_log):
                    raise ValueError(f"Singlet job for {molecule} is not completed yet.")
                if not check_job_completion(triplet_log):
                    raise ValueError(f"Triplet job for {molecule} is not completed yet.")

                if os.path.exists(singlet_log):
                    with open(singlet_log, 'r') as file_s:
                        content_s = file_s.read()
                        print(f"[DEBUG] Content of singlet log (first 500 chars): {content_s[:500]}")
                        s0_match = s0_pattern.search(content_s)  # Ground state energy
                        s1_match = s1_pattern.search(content_s)  # Singlet state energy
                        if s0_match and s1_match:
                            s0 = float(s0_match.group(1))  # Extract s0
                            s1 = float(s1_match.group(1))  # Extract s1
                            print(f"[DEBUG] {molecule} Singlet file: s0 = {s0}, s1 = {s1}")
                        else:
                            raise ValueError(f"Failed to extract s0 or s1 data from {singlet_log}.")
                else:
                    raise FileNotFoundError(f"Log file not found: {singlet_log}")

                if os.path.exists(triplet_log):
                    with open(triplet_log, 'r') as file_t:
                        content_t = file_t.read()
                        print(f"[DEBUG] Content of triplet log (first 500 chars): {content_t[:500]}")
                        t1_match = t1_pattern.search(content_t)  # Triplet state energy
                        if t1_match:
                            t1 = float(t1_match.group(1))  # Extract t1
                            print(f"[DEBUG] {molecule} Triplet file: t1 = {t1}")
                        else:
                            raise ValueError(f"Failed to extract t1 data from {triplet_log}.")
                else:
                    raise FileNotFoundError(f"Log file not found: {triplet_log}")

                # Calculate S1, T1, and S1-T1 difference
                S1 = (s1 - s0) * 27.2114  # Convert from Hartree to eV
                T1 = (t1 - s0) * 27.2114  # Convert from Hartree to eV
                s1_t1_gap = S1 - T1

                print(f"[DEBUG] Calculated S1: {S1}, T1: {T1}, S1-T1: {s1_t1_gap}")

                # Append data for this molecule
                data.append({
                    "molecule": molecule,
                    "a1": a1,
                    "b1": b1,
                    "a2": a2,
                    "b2": b2,
                    "S1": S1,
                    "T1": T1,
                    "S1-T1": s1_t1_gap
                })
                break  # If successful, stop retrying

            except (ValueError, FileNotFoundError) as e:
                print(f"[ERROR] {e}")
                retry_count += 1
                if retry_count < 2:
                    print(f"Retrying job for {molecule}...")
                    if "singlet" in str(e).lower():
                        rerun_job(molecule, a1, b1, a2, b2, state='S')  # Resubmit singlet job
                    elif "triplet" in str(e).lower():
                        rerun_job(molecule, a1, b1, a2, b2, state='T')  # Resubmit triplet job
                else:
                    print(f"Skipping molecule {molecule} after failed retries.")
                    continue

    return data

def save_extracted_data_to_csv(extracted_data, filename='extracted_data.csv'):
    if extracted_data:  
        keys = extracted_data[0].keys()  
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(extracted_data)
        print(f"Data successfully saved to {filename}")
    else:
        print("[WARNING] No data to save!")

def calculate_rmse_mae(comparison_results):
    differences = [result['S1_T1_diff'] for result in comparison_results]

    if all(diff < 0 for diff in differences):
        # Calculate RMSE
        mse = sum(diff ** 2 for diff in differences) / len(differences)
        rmse = math.sqrt(mse)

        # Calculate MAE
        mae = sum(abs(diff) for diff in differences) / len(differences)

        return rmse, mae
    else:
        print("Some S1-T1 differences are positive, skipping this combination.")
        return None, None

