#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 input_file"
    exit 1
fi

input_file="$1"
min_rmse=999999
min_mae=999999
min_rmse_combination=""
min_mae_combination=""
current_combination=""

while IFS= read -r line; do
    # Capture the combination line
    if [[ $line == Combination:* ]]; then
        current_combination="$line"
    # Process the RMSE/MAE line
    elif [[ $line == RMSE:* ]]; then
        # Extract RMSE and MAE using sed
        rmse=$(echo "$line" | sed -E 's/.*RMSE: ([0-9.]+),.*/\1/')
        mae=$(echo "$line" | sed -E 's/.*MAE: ([0-9.]+).*/\1/')
        
        # Compare and update minimum RMSE
        if (( $(echo "$rmse < $min_rmse" | bc -l) )); then
            min_rmse="$rmse"
            min_rmse_combination="$current_combination"
        fi
        
        # Compare and update minimum MAE
        if (( $(echo "$mae < $min_mae" | bc -l) )); then
            min_mae="$mae"
            min_mae_combination="$current_combination"
        fi
    fi
done < "$input_file"

echo "Combination with smallest RMSE:"
echo "$min_rmse_combination"
echo "RMSE: $min_rmse"
echo ""
echo "Combination with smallest MAE:"
echo "$min_mae_combination"
echo "MAE: $min_mae"

