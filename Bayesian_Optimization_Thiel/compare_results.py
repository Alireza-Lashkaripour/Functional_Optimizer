#!/usr/bin/env python3

import csv
import math


def compare_with_reference(extracted_data, VEE_ref):
    comparison = []
    valid_differences = []
    skipped_molecules = []

    for entry in extracted_data:
        molecule = entry['molecule']
        try:
            vee_values = [float(value) for key, value in entry.items() if key.startswith('VEE_')]
            vee_ref_values = VEE_ref.get(molecule, [])

            if vee_ref_values and len(vee_values) == len(vee_ref_values):
                differences = [abs(vee - ref) for vee, ref in zip(vee_values, vee_ref_values)]
                valid_differences.extend(differences)

                molecule_comparison = {
                    'molecule': molecule,
                    'VEE_calculated': vee_values,
                    'VEE_reference': vee_ref_values,
                    'VEE_diff': differences
                }
                comparison.append(molecule_comparison)
            else:
                print(f"Skipping molecule {molecule} due to mismatched reference values or missing data.")
                skipped_molecules.append(molecule)

        except ValueError as e:
            print(f"Error processing molecule {molecule}: {e}")
            skipped_molecules.append(molecule)
            continue

    print(f"Skipped {len(skipped_molecules)} molecules due to mismatched reference values or errors.")
    return comparison, valid_differences


def calculate_rmse_mae(differences):
    if not differences:
        print("No valid differences for RMSE/MAE calculation.")
        return None, None

    mse = sum(diff ** 2 for diff in differences) / len(differences)
    rmse = math.sqrt(mse)
    mae = sum(abs(diff) for diff in differences) / len(differences)

    return rmse, mae


def save_summary_results(params, rmse, mae, comparison_results, filename='results_summary.txt'):
    with open(filename, 'a') as f:
        f.write(
            f"Combination: a1={params['a1']}, b1={params['b1']}, a2={params['a2']}, b2={params['b2']}, co={params['co']}, ov={params['ov']}, cv={params['cv']}, mrmu={params['mrmu']}, mu={params['mu']}\n"
        )
        f.write(f"RMSE: {rmse}, MAE: {mae}\n")
        f.write("Per-molecule differences:\n")
        for result in comparison_results:
            vee_diffs = ', '.join([f"{diff:.4f}" for diff in result['VEE_diff']])
            f.write(f"{result['molecule']}: VEE_diff={vee_diffs}\n")
        f.write("\n")


VEE_ref = {
    "Ethene": [7.8],
    "E-Butadiene": [6.18, 6.55]
}


def load_extracted_data_from_csv(filename='extracted_data.csv'):
    extracted_data = []
    try:
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                extracted_data.append(row)
        print(f"Data loaded from {filename}")
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
    except Exception as e:
        print(f"Error reading {filename}: {e}")

    return extracted_data


def save_comparison_results_to_csv(comparison_data, filename='comparison_results.csv'):
    if comparison_data:
        keys = comparison_data[0].keys()
        try:
            with open(filename, 'w', newline='') as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(comparison_data)
            print(f"Comparison data successfully saved to {filename}")
        except Exception as e:
            print(f"Error saving data to {filename}: {e}")
    else:
        print("No comparison data to save.")


extracted_data = load_extracted_data_from_csv('extracted_data.csv')
comparison_results, valid_differences = compare_with_reference(extracted_data, VEE_ref)
save_comparison_results_to_csv(comparison_results, 'comparison_results.csv')

rmse, mae = calculate_rmse_mae(valid_differences)

if rmse is not None and mae is not None:
    print(f"RMSE: {rmse}, MAE: {mae}")
    save_summary_results(
        params={
            "a1": "N/A",
            "b1": "N/A",
            "a2": "N/A",
            "b2": "N/A",
            "co": "N/A",
            "ov": "N/A",
            "cv": "N/A",
            "mrmu": "N/A",
            "mu": "N/A"
        },
        rmse=rmse,
        mae=mae,
        comparison_results=comparison_results
    )
else:
    print("RMSE and MAE calculation skipped due to invalid differences.")

for result in comparison_results:
    vee_diffs = ', '.join([f"{diff:.4f}" for diff in result['VEE_diff']])
    print(f"Molecule: {result['molecule']}")
    print(f"VEE Differences: {vee_diffs}\n")

