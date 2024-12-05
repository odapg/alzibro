#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import zipfile
import os
import json
import shutil
import tempfile
import subprocess

from alfred import alfred_error_message, outcome_JSON

def temp_extract_and_quicklook(zip_file, to_extract, next_directory):
    # Extracts a file in a temporary folder and takes a Quicklook at it
    
    alzibro_data_folder = os.getenv('alfred_workflow_data')

    with tempfile.TemporaryDirectory() as temp_dir:
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
        ql_exe = os.path.join(alzibro_data_folder, 'ql')
        if os.path.isfile(ql_exe):
            ql_shell_command = ql_exe
            ql_options = ""
        else:
            ql_shell_command = "qlmanage" 
            ql_options = "-p"
        subprocess.run([ql_shell_command, ql_options, temp_file], shell=False, check=True)
        
        # Pass variables to the External Call that reruns the workflow
        comment = ""
        ResultJSON = outcome_JSON(next_directory, comment, zip_file)
        print(json.dumps(ResultJSON))

        
def main():
    zip_file = os.getenv('zip_file')
    to_extract = os.getenv('file_to_extract')
    next_directory = os.getenv('next_directory')
    temp_extract_and_quicklook(zip_file, to_extract, next_directory)

if __name__ == "__main__":
    main()

