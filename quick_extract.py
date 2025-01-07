#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import zipfile
import os
import json
import shutil
import subprocess

from alfred import alfred_error_message, outcome_JSON, selection_error_message

def temp_extract_and_quicklook(zip_file, to_extract, next_directory):
    # Extracts a file in a temporary folder and takes a Quicklook at it
    
    cache_folder = os.getenv('alfred_workflow_cache')
    temp_dir = os.path.join(cache_folder, 'quicklook_files')

    if not os.path.isdir(temp_dir):
        try:
            os.mkdir(temp_dir)
        except Exception as e:
            comment = f"Error creating quicklook files folder" 
            subcomment = str(e)
            selection_error_message(comment, subcomment)
            sys.exit()

    # Extraction
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        try:
            zip_ref.extract(to_extract, temp_dir)            
        except Exception as e:
            comment = "Error: " + str(e)
            alfred_error_message(comment, next_directory, zip_file)
            return

    # Quicklook with ql if possible, with qlmanage -p otherwise
    temp_file = os.path.join(temp_dir, to_extract)
    
    # Pass variables to the External Call that reruns the workflow
    comment = ""
    ResultJSON = outcome_JSON(next_directory, comment, zip_file, to_reveal=temp_file)
    print(json.dumps(ResultJSON))

        
def main():
    zip_file = os.getenv('zip_file')
    to_extract = os.getenv('file_to_extract')
    next_directory = os.getenv('next_directory')
    temp_extract_and_quicklook(zip_file, to_extract, next_directory)

if __name__ == "__main__":
    main()

