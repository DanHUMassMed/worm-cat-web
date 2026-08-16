#!/bin/bash

# Replace 'path/to/directory' with the actual path of the directory you want to process.
directory_path="worm_cat"
#directory_path="worm_cat/static/dynamic"

# List of criteria to identify directories for deletion
#criteria=("!" "�" "Laziest" "uick" "You" "you" "oogle" "yy)
criteria=("_Jan-" "_Feb-" "_Mar-" "_Apr-" "_May-" "_Jun-" "_Jul-" "_Aug-" "_Sep-" "_Oct-" "_Nov-" "_Dec-")

# Function to check if a directory name contains any of the specified criteria
function contains_criteria() {
  local dir_name=$1
  for crit in "${criteria[@]}"; do
    if [[ $dir_name == *"$crit"* ]]; then
      return 0
    fi
  done
  return 1
}

# List all directories within the specified directory and store them in an array.
directories=( "$directory_path"/*/ )

# Loop through the directories array.
for dir in "${directories[@]}"; do
  # Get the directory name without the path.
  dir_name=$(basename "$dir")
  
  # Check if the directory name contains any of the specified criteria.
  if contains_criteria "$dir_name"; then
    echo "Deleting directory: $dir_name"
    # Remove the directory recursively using 'rm' command.
    rm -r "$dir"
  fi
done

