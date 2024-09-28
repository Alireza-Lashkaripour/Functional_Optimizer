#!/usr/bin/env python3

from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from generate_and_submit_jobs import generate_input_files_and_submit
from extract_log_data import extract_log_data, save_extracted_data_to_csv
from compare_results import compare_with_reference, S1_ref, T1_ref, calculate_rmse_mae
import csv

space = {
    'a1': hp.uniform('a1', 0.45, 0.55),
    'b1': hp.uniform('b1', -0.28, -0.18),
    'a2': hp.uniform('a2', 0.60, 0.75),
    'b2': hp.uniform('b2', -0.12, -0.08)
}

molecules = ["Heptazine", "Cyclazine", "Molecule3", "Molecule4", "Molecule5",
             "Molecule6", "Molecule7", "Molecule8", "Molecule9", "Molecule10"]

# Define max jobs for parallel submissions(better keep it 20)
max_jobs = 20

best_result = {'rmse': float('inf'), 'params': None}

def save_results_summary(params, rmse, mae, comparison_results, filename='results_summary.txt'):
    with open(filename, 'a') as f:
        f.write(f"Combination: a1={params['a1']}, b1={params['b1']}, a2={params['a2']}, b2={params['b2']}\n")
        f.write(f"RMSE: {rmse}, MAE: {mae}\n")
        f.write("Per-molecule differences:\n")
        for result in comparison_results:
            f.write(f"{result['molecule']}: S1_diff={result['S1_diff']}, T1_diff={result['T1_diff']}, S1_T1_diff={result['S1_T1_diff']}\n")
        f.write("\n")

def objective(params):
    global best_result
    
    a1 = round(params['a1'], 2)
    b1 = round(params['b1'], 2)
    a2 = round(params['a2'], 2)
    b2 = round(params['b2'], 2)

    print(f"Trying combination: a1={a1}, b1={b1}, a2={a2}, b2={b2}")

    job_ids_s = generate_input_files_and_submit(molecules, a1, b1, a2, b2, state='S', max_jobs=max_jobs)
    job_ids_t = generate_input_files_and_submit(molecules, a1, b1, a2, b2, state='T', max_jobs=max_jobs)

    job_ids = job_ids_s + job_ids_t

    print("Waiting for all jobs to complete and extracting data.")
    extracted_data = extract_log_data(molecules, a1, b1, a2, b2, job_ids)

    save_extracted_data_to_csv(extracted_data, 'extracted_data.csv')

    comparison_results, valid_differences = compare_with_reference(extracted_data, S1_ref, T1_ref)

    rmse, mae = calculate_rmse_mae(valid_differences)

    if rmse is not None and mae is not None:
        print(f"RMSE: {rmse}, MAE: {mae}")

        save_results_summary(params, rmse, mae, comparison_results)

        if rmse < best_result['rmse']:
            best_result['rmse'] = rmse
            best_result['params'] = params

        return {'loss': rmse, 'status': STATUS_OK}
    else:
        print(f"Skipping combination due to positive S1-T1 values.")
        return {'loss': float('inf'), 'status': STATUS_OK}

trials = Trials()

best = fmin(objective, space, algo=tpe.suggest, max_evals=2500, trials=trials)

with open('results_summary.txt', 'a') as f:
    f.write(f"\nBest Parameters Found: a1={best_result['params']['a1']}, b1={best_result['params']['b1']}, ")
    f.write(f"a2={best_result['params']['a2']}, b2={best_result['params']['b2']}\n")
    f.write(f"Best RMSE: {best_result['rmse']}\n")

print("Best parameters found:", best_result)

