#!/usr/bin/env python3

from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from generate_and_submit_jobs import generate_and_submit_jobs
from extract_log_data import extract_log_data, save_extracted_data_to_csv
from compare_results import compare_with_reference, VEE_ref, calculate_rmse_mae
import csv


space = {
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

molecules = ["Ethene", "E-Butadiene"]

max_jobs = 20

best_result = {'rmse': float('inf'), 'params': None}


def save_results_summary(params, rmse, mae, comparison_results, filename='results_summary.txt'):
    with open(filename, 'a') as f:
        f.write(
            f"Combination: a1={params['a1']}, b1={params['b1']}, a2={params['a2']}, b2={params['b2']}, co={params['co']}, "
            f"ov={params['ov']}, cv={params['cv']}, mrmu={params['mrmu']}, mu={params['mu']}\n"
        )
        f.write(f"RMSE: {rmse}, MAE: {mae}\n")
        f.write("Per-molecule differences:\n")
        for result in comparison_results:
            vee_diffs = ', '.join([f"{diff:.4f}" for diff in result['VEE_diff']])
            f.write(f"{result['molecule']}: VEE_diff={vee_diffs}\n")
        f.write("\n")


def round_params(params):
    return {key: round(value, 2) for key, value in params.items()}


def objective(params):
    global best_result

    params = round_params(params)
    a1, b1, a2, b2, co, ov, cv, mrmu, mu = (
        params['a1'], params['b1'], params['a2'], params['b2'],
        params['co'], params['ov'], params['cv'], params['mrmu'], params['mu']
    )

    print(
        f"Trying combination: a1={a1}, b1={b1}, a2={a2}, b2={b2}, co={co}, ov={ov}, cv={cv}, mrmu={mrmu}, mu={mu}"
    )

    job_ids = generate_and_submit_jobs(
        molecules, a1, b1, a2, b2, co, ov, cv, mrmu, mu, max_jobs=max_jobs
    )

    print("Waiting for all jobs to complete and extracting data.")
    extracted_data = extract_log_data(
        molecules, a1, b1, a2, b2, co, ov, cv, mrmu, mu, job_ids
    )

    save_extracted_data_to_csv(extracted_data, 'extracted_data.csv')

    comparison_results, valid_differences = compare_with_reference(extracted_data, VEE_ref)

    rmse, mae = calculate_rmse_mae(valid_differences)

    if rmse is not None and mae is not None:
        print(f"RMSE: {rmse}, MAE: {mae}")
        save_results_summary(params, rmse, mae, comparison_results)

        if rmse < best_result['rmse']:
            best_result['rmse'] = rmse
            best_result['params'] = params

        return {'loss': rmse, 'status': STATUS_OK}
    else:
        print("Skipping combination due to invalid VEE differences.")
        return {'loss': float('inf'), 'status': STATUS_OK}


trials = Trials()

best = fmin(objective, space, algo=tpe.suggest, max_evals=5, trials=trials)

if best_result['params'] is not None:
    with open('results_summary.txt', 'a') as f:
        f.write(
            f"\nBest Parameters Found: a1={best_result['params']['a1']}, b1={best_result['params']['b1']}, "
            f"a2={best_result['params']['a2']}, b2={best_result['params']['b2']}\n"
            f"co={best_result['params']['co']}, ov={best_result['params']['ov']}\n"
            f"cv={best_result['params']['cv']}, mrmu={best_result['params']['mrmu']}, mu={best_result['params']['mu']}\n"
            f"Best RMSE: {best_result['rmse']}\n"
        )
    print("Best parameters found:", best_result)
else:
    print("No valid parameters were found during optimization. Please check the logs and job submissions.")

