#!/usr/bin/env python3


import os
import re
import csv
import subprocess
from time import sleep
import math

def rerun_job(molecule, a1, b1, a2, b2, co, ov, cv, mrmu, mu):
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_co_{co}_ov_{ov}_cv_{cv}_mrmu_{mrmu}_mu_{mu}'
    inp_file = f"{molecule}_{state_dir}.inp"
    current_dir = os.getcwd()
    job_dir = os.path.join(current_dir, state_dir)

    if not os.path.exists(job_dir):
        print(f"Directory {job_dir} does not exist.")
        return None

    try:
        os.chdir(job_dir)
        print(f"Rerunning job for {molecule} in directory {job_dir}...")
        job_submission_command = f"gms_sbatch -p trd -n 30 -i {inp_file}"
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
    if os.path.exists(log_file):
        with open(log_file, 'r') as log:
            content = log.read()
            if "CPU timing information for all processes" in content or "ddikick.x: exited gracefully." in content:
                return True
    return False


def extract_log_data(molecules, a1, b1, a2, b2, co, ov, cv, mrmu, mu, job_ids):
    ensure_job_completion(job_ids)
    state_dir = f'a1_{a1}_b1_{b1}_a2_{a2}_b2_{b2}_co_{co}_ov_{ov}_cv_{cv}_mrmu_{mrmu}_mu_{mu}'
    data = []

    for molecule in molecules:
        vee_log = os.path.join(state_dir, f"{molecule}_{state_dir}.log")
        print(f"\nProcessing molecule: {molecule}")
        print(f"VEE log path: {vee_log}")

        retry_count = 0
        while retry_count < 2:
            try:
                if not os.path.exists(vee_log):
                    raise FileNotFoundError(f"Log file not found: {vee_log}")
                if not check_job_completion(vee_log):
                    raise ValueError(f"Job for {molecule} is not completed yet.")

                command = f"./3_read.sh {molecule} {vee_log}"
                result = subprocess.check_output(command, shell=True, universal_newlines=True).strip()
                print(f"[DEBUG] AWK Output: {result}")

                if "has problem" in result:
                    raise ValueError(f"SCF convergence issue detected for {molecule}")

                extracted_values = []
                for line in result.splitlines():
                    parts = line.split()
                    if len(parts) == 2:
                        mol_name, vee = parts
                        extracted_values.append(float(vee))

                if not extracted_values:
                    raise ValueError(f"No valid VEE values found for {molecule}")

                molecule_data = {
                    "molecule": molecule,
                    "a1": a1,
                    "b1": b1,
                    "a2": a2,
                    "b2": b2,
                    "co": co,
                    "ov": ov,
                    "cv": cv,
                    "mrmu": mrmu,
                    "mu": mu,
                }

                for idx, vee in enumerate(extracted_values):
                    molecule_data[f"VEE_{idx + 1}"] = vee

                data.append(molecule_data)
                print(f"[INFO] Successfully extracted VEE data for {molecule}: {extracted_values}")
                break

            except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"[ERROR] {e}")
                retry_count += 1
                if retry_count < 2:
                    print(f"Retrying job for {molecule}...")
                    rerun_job(molecule, a1, b1, a2, b2, co, ov, cv, mrmu, mu)
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
    differences = [result['VEE_1'] for result in comparison_results if 'VEE_1' in result]

    if all(diff < 0 for diff in differences):
        mse = sum(diff ** 2 for diff in differences) / len(differences)
        rmse = math.sqrt(mse)
        mae = sum(abs(diff) for diff in differences) / len(differences)
        return rmse, mae
    else:
        print("Some VEE values are positive, skipping this combination.")
        return None, None

