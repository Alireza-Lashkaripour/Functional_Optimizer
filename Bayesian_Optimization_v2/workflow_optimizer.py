#!/usr/bin/env python3

import os
import subprocess
import math
import csv
from time import sleep
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
import yaml
import logging

# --- 1. CONFIGURATION AND LOGGING -----------------------------------------

logging.basicConfig(
    filename='workflow.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(config_file='default_config.yaml'):
    """Load configuration from a YAML file."""
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)


# --- 2. JOB MANAGER -------------------------------------------------------

class JobManager:
    """Handles job file generation, submission, and monitoring."""

    def __init__(self, geometry_file, max_jobs):
        self.geometry_file = geometry_file
        self.max_jobs = max_jobs

    def generate_input_files(self, molecule, params, state):
        """Generate input files for each molecule."""
        state_dir = f"a1_{params['a1']}_b1_{params['b1']}_a2_{params['a2']}_b2_{params['b2']}_{state}"
        if not os.path.exists(state_dir):
            os.makedirs(state_dir)
        
        inp_file = os.path.join(state_dir, f"{molecule}_{state_dir}.inp")
        try:
            command = f'./gen_geo.sh {molecule} {self.geometry_file}'
            geom_data = subprocess.check_output(command, shell=True).decode()
            with open(inp_file, 'w') as f:
             f.write(f""" $CONTRL SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp
 ICHARG=0 TDDFT=MRSF MAXIT=200 
 MULT=3 ISPHER=0 UNITS=BOHR $END
 $TDDFT NSTATE=3 IROOT=1 MULT={'1' if state == 'S' else '3'} 
 mralp={params['a2']} mrbet={params['b2']} $END
 $TDDFT spcp(1)=0.5,0.5,0.5 $END
 $DFT alphac={params['a1']} betac={params['b1']} $END
 $SCF DIRSCF=.t. diis=.f. damp=.t. soscf=.f. shift=.t.
 FDIFF=.t. $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $SYSTEM TIMLIM=999999100 MWORDS=500 kdiag=1 $END
 $DATA
 {molecule}
 C1
""")
            f.write(geom_data)
            logging.info(f"Generated input file for {molecule}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to generate input for {molecule}: {e}")

    def submit_job(self, molecule, params, state):
        """Submit a computational job."""
        state_dir = f"a1_{params['a1']}_b1_{params['b1']}_a2_{params['a2']}_b2_{params['b2']}_{state}"
        inp_file = f"{molecule}_{state_dir}.inp"
        try:
            job_id = subprocess.check_output(
                f"gms_sbatch -p r630 -c 30 -i {inp_file}",
                shell=True,
                cwd=state_dir
            ).decode().strip()
            logging.info(f"Job submitted for {molecule} with ID: {job_id}")
            return job_id
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to submit job for {molecule}: {e}")
            return None


# --- 3. DATA EXTRACTOR ----------------------------------------------------


class DataExtractor:
    """Extract data from computational log files."""

    def __init__(self, config):
        self.config = config
        self.retry_limit = 2  # Number of retries for failed extractions

    def rerun_job(self, molecule, params, state):
        """Resubmit a failed job."""
        state_dir = f"a1_{params['a1']}_b1_{params['b1']}_a2_{params['a2']}_b2_{params['b2']}_{state}"
        inp_file = f"{molecule}_{state_dir}.inp"

        current_dir = os.getcwd()
        job_dir = os.path.join(current_dir, state_dir)

        if not os.path.exists(job_dir):
            logging.error(f"Directory {job_dir} does not exist.")
            return None

        try:
            os.chdir(job_dir)
            logging.info(f"Rerunning job for {molecule} in directory {job_dir}...")
            job_submission_command = f"gms_sbatch -p r630 -c 30 -i {inp_file}"
            job_id = subprocess.check_output(job_submission_command, shell=True).strip().decode()
            logging.info(f"Job resubmitted with ID: {job_id}")
            self.wait_for_jobs_to_finish([job_id])
            os.chdir(current_dir)
            return job_id
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to resubmit job for {molecule}. Error: {e}")
            os.chdir(current_dir)
            return None

    def wait_for_jobs_to_finish(self, job_ids):
        """Wait until specific jobs are completed."""
        while job_ids:
            for job_id in list(job_ids):
                logging.info(f"Waiting for job {job_id} to complete...")
                try:
                    result = subprocess.run(
                        f"squeue -j {job_id}",
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    if job_id not in result.stdout.decode():
                        logging.info(f"Job {job_id} has completed.")
                        job_ids.remove(job_id)
                    else:
                        logging.info(f"Job {job_id} is still running. Waiting...")
                except Exception as e:
                    logging.error(f"Error checking status for job {job_id}: {e}")
            time.sleep(30)

    def check_job_completion(self, log_file):
        """Check for successful job completion."""
        if os.path.exists(log_file):
            with open(log_file, 'r') as log:
                content = log.read()
                return "CPU timing information" in content or "ddikick.x: exited gracefully." in content
        return False

    def extract_data(self, molecules, params):
        """Extract data from GAMESS log files."""
        data = []

        singlet_dir = f"a1_{params['a1']}_b1_{params['b1']}_a2_{params['a2']}_b2_{params['b2']}_S"
        triplet_dir = f"a1_{params['a1']}_b1_{params['b1']}_a2_{params['a2']}_b2_{params['b2']}_T"

        s0_pattern = re.compile(r"1\s+A\s+([-+]?\d*\.\d+|\d+)")
        s1_pattern = re.compile(r"2\s+A\s+([-+]?\d*\.\d+|\d+)")
        t1_pattern = re.compile(r"1\s+A\s+([-+]?\d*\.\d+|\d+)")

        for molecule in molecules:
            logging.info(f"Processing molecule: {molecule}")

            singlet_log = os.path.join(singlet_dir, f"{molecule}_{singlet_dir}.log")
            triplet_log = os.path.join(triplet_dir, f"{molecule}_{triplet_dir}.log")

            retry_count = 0
            while retry_count < self.retry_limit:
                try:
                    if not self.check_job_completion(singlet_log):
                        raise ValueError(f"Singlet job for {molecule} is not completed yet.")
                    if not self.check_job_completion(triplet_log):
                        raise ValueError(f"Triplet job for {molecule} is not completed yet.")

                    with open(singlet_log, 'r') as file_s:
                        content_s = file_s.read()
                        s0_match = s0_pattern.search(content_s)
                        s1_match = s1_pattern.search(content_s)
                        if not (s0_match and s1_match):
                            raise ValueError("Failed to extract s0 or s1 from singlet log.")
                        s0 = float(s0_match.group(1))
                        s1 = float(s1_match.group(1))

                    with open(triplet_log, 'r') as file_t:
                        content_t = file_t.read()
                        t1_match = t1_pattern.search(content_t)
                        if not t1_match:
                            raise ValueError("Failed to extract t1 from triplet log.")
                        t1 = float(t1_match.group(1))

                    S1 = (s1 - s0) * 27.2114
                    T1 = (t1 - s0) * 27.2114
                    s1_t1_gap = S1 - T1

                    data.append({
                        "molecule": molecule,
                        "a1": params['a1'],
                        "b1": params['b1'],
                        "a2": params['a2'],
                        "b2": params['b2'],
                        "S1": S1,
                        "T1": T1,
                        "S1-T1": s1_t1_gap
                    })

                    logging.info(f"[SUCCESS] Extracted data for {molecule}: S1={S1}, T1={T1}, Gap={s1_t1_gap}")
                    break

                except (ValueError, FileNotFoundError) as e:
                    logging.error(f"[ERROR] {e}")
                    retry_count += 1
                    if retry_count < self.retry_limit:
                        if "singlet" in str(e).lower():
                            self.rerun_job(molecule, params, state='S')
                        elif "triplet" in str(e).lower():
                            self.rerun_job(molecule, params, state='T')
                    else:
                        logging.error(f"Skipping molecule {molecule} after failed retries.")

        return data

# --- 4. COMPARATOR --------------------------------------------------------

class Comparator:
    """Compare extracted data with reference values."""

    def compare_with_reference(self, data, ref_S1, ref_T1):
        comparison = []
        valid_differences = []
        for entry in data:
            molecule = entry['molecule']
            S1_diff = abs(entry['S1'] - ref_S1.get(molecule, 0))
            T1_diff = abs(entry['T1'] - ref_T1.get(molecule, 0))
            S1_T1_diff = abs(entry['S1-T1'] - (ref_S1.get(molecule, 0) - ref_T1.get(molecule, 0)))

            comparison.append({
                'molecule': molecule,
                'S1_diff': S1_diff,
                'T1_diff': T1_diff,
                'S1_T1_diff': S1_T1_diff
            })
            valid_differences.append(S1_T1_diff)
        return comparison, valid_differences


# --- 5. OPTIMIZER ---------------------------------------------------------

class Optimizer:
    """Optimize parameters using Bayesian Optimization."""

    def __init__(self, config):
        self.config = config

    def objective(self, params):
        job_manager = JobManager(self.config['geometry_file'], self.config['optimization']['max_jobs'])
        extractor = DataExtractor()
        comparator = Comparator()

        for molecule in self.config['molecules']:
            job_manager.generate_input_files(molecule, params, state='S')
            job_manager.submit_job(molecule, params, state='S')

        data = extractor.extract_data(self.config['molecules'], params)
        _, valid_diffs = comparator.compare_with_reference(data, self.config['reference_values']['S1'], self.config['reference_values']['T1'])

        if valid_diffs:
            rmse = math.sqrt(sum(d**2 for d in valid_diffs) / len(valid_diffs))
            return {'loss': rmse, 'status': STATUS_OK}
        return {'loss': float('inf'), 'status': STATUS_OK}

    def run(self):
        space = {
            'a1': hp.uniform('a1', *self.config['parameters']['a1']),
            'b1': hp.uniform('b1', *self.config['parameters']['b1']),
            'a2': hp.uniform('a2', *self.config['parameters']['a2']),
            'b2': hp.uniform('b2', *self.config['parameters']['b2'])
        }
        best = fmin(self.objective, space, algo=tpe.suggest, max_evals=self.config['optimization']['max_evals'], trials=Trials())
        print("Best parameters:", best)


# --- 6. MAIN WORKFLOW -----------------------------------------------------

if __name__ == "__main__":
    config = load_config()
    optimizer = Optimizer(config)
    optimizer.run()

