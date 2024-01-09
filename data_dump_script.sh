#!/bin/bash

echo "Please provide the command for dumping/archiving:"
read -r custom_command

echo "Enter the source folder:"
read -r source_folder

echo "Enter the destination folder:"
read -r destination_folder

if [ ! -d "$destination_folder" ]; then
    mkdir -p "$destination_folder"
fi

if [ -d "$destination_folder" ]; then
    # Execute the user-provided command with source and destination folders
    eval "$custom_command" "$source_folder" "$destination_folder"
else
    echo "Failed to create destination folder or it does not exist. Exiting..."
    exit 1
fi
