#!/usr/bin/env python3

import csv
import math

def compare_with_reference(extracted_data, S1_ref, T1_ref):
    comparison = []
    valid_differences = []  
    skipped_molecules = []  

    for entry in extracted_data:
        molecule = entry['molecule']
        try:
            S1 = float(entry['S1'])
            T1 = float(entry['T1'])
            S1_T1_gap = float(entry['S1-T1'])

            S1_ref_val = S1_ref.get(molecule, None)
            T1_ref_val = T1_ref.get(molecule, None)

            if S1_ref_val is not None and T1_ref_val is not None:
                S1_T1_ref_val = S1_ref_val - T1_ref_val

                S1_diff = abs(S1 - S1_ref_val)
                T1_diff = abs(T1 - T1_ref_val)
                S1_T1_diff = abs(S1_T1_gap - S1_T1_ref_val)

                comparison.append({
                    'molecule': molecule,
                    'S1_calculated': S1,
                    'S1_reference': S1_ref_val,
                    'S1_diff': S1_diff,
                    'T1_calculated': T1,
                    'T1_reference': T1_ref_val,
                    'T1_diff': T1_diff,
                    'S1_T1_diff': S1_T1_diff
                })

                if S1_T1_gap < 0:  
                    valid_differences.append(S1_T1_diff)
                else:
                    print(f"Skipping molecule {molecule} due to positive S1-T1 gap.")
                    skipped_molecules.append(molecule)
            else:
                print(f"Warning: No reference values found for molecule {molecule}")
                skipped_molecules.append(molecule)

        except ValueError as e:
            print(f"Error processing molecule {molecule}: {e}")
            skipped_molecules.append(molecule)
            continue

    print(f"Skipped {len(skipped_molecules)} molecules due to issues (positive S1-T1 gap or missing reference data).")
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
        f.write(f"Combination: a1={params['a1']}, b1={params['b1']}, a2={params['a2']}, b2={params['b2']}\n")
        f.write(f"RMSE: {rmse}, MAE: {mae}\n")
        f.write("Per-molecule differences:\n")
        for result in comparison_results:
            f.write(f"{result['molecule']}: S1_diff={result['S1_diff']}, T1_diff={result['T1_diff']}, S1_T1_diff={result['S1_T1_diff']}\n")
        f.write("\n")

S1_ref = {
    "Heptazine": 2.717, "Cyclazine": 0.979, "Molecule3": 1.562, "Molecule4": 2.177,
    "Molecule5": 2.127, "Molecule6": 0.833, "Molecule7": 0.693, "Molecule8": 0.554,
    "Molecule9": 1.264, "Molecule10": 1.522
}

T1_ref = {
    "Heptazine": 2.936, "Cyclazine": 1.110, "Molecule3": 1.663, "Molecule4": 2.296,
    "Molecule5": 2.230, "Molecule6": 0.904, "Molecule7": 0.735, "Molecule8": 0.583,
    "Molecule9": 1.463, "Molecule10": 1.827
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
        print(f"No comparison data to save.")

extracted_data = load_extracted_data_from_csv('extracted_data.csv')

comparison_results, valid_differences = compare_with_reference(extracted_data, S1_ref, T1_ref)

save_comparison_results_to_csv(comparison_results, 'comparison_results.csv')

rmse, mae = calculate_rmse_mae(valid_differences)

if rmse is not None and mae is not None:
    print(f"RMSE: {rmse}, MAE: {mae}")
    save_summary_results(params={"a1": "N/A", "b1": "N/A", "a2": "N/A", "b2": "N/A"}, rmse=rmse, mae=mae, comparison_results=comparison_results)
else:
    print("RMSE and MAE calculation skipped due to invalid differences.")

for result in comparison_results:
    print(f"Molecule: {result['molecule']}")
    print(f"S1 Calculated: {result['S1_calculated']}, S1 Reference: {result['S1_reference']}, S1 Difference: {result['S1_diff']}")
    print(f"T1 Calculated: {result['T1_calculated']}, T1 Reference: {result['T1_reference']}, T1 Difference: {result['T1_diff']}")
    print(f"S1-T1 Difference: {result['S1_T1_diff']}\n")

