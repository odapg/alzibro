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

def notify_and_reveal(comment, next_directory, to_extract, destination_folder, zip_file):
    
    reveal = os.path.join(destination_folder, to_extract)
    ResultJSON = outcome_JSON(next_directory, comment, zip_file, to_reveal=reveal)
    print(json.dumps(ResultJSON))    

def extract_folder_from_zip(zip_file, to_extract, next_directory):
    '''
     zip_file = the processed .zip file 
     to_extract = the file of folder to extract
     next_directory = the folder to be visited afterwards if Alzibro is not closed after extraction
    '''

    if not os.path.isfile(zip_file):
        comment = f"Error: the file '{zip_file}' was not found."
        alfred_error_message(comment, next_directory, zip_file)
        return

    zip_directory, zip_name = os.path.split(zip_file)
    zip_name = os.path.splitext(zip_name)[0]

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            files_to_extract = [f for f in zip_ref.namelist() if f.startswith(to_extract)]
            if not files_to_extract:
                comment = f"Error: the path '{to_extract}' was not found in the ZIP file."
                alfred_error_message(comment, next_directory, zip_file)
                return
            
            # Extraction
            output_folder = os.path.join(temp_dir, to_extract)
            
            for file in files_to_extract:
                my_dir = os.path.dirname(file.rstrip('/'))
                zip_ref.extract(file, temp_dir + '/' + zip_name + '/')
                # If there was associated metadata, retrieve them            
                if my_dir == "":
                    macosx_weird_file = '__MACOSX/'+ my_dir \
                                        + '._' + os.path.basename(file)
                else:
                    macosx_weird_file = '__MACOSX/'+ my_dir \
                                        + '/._' + os.path.basename(file)
                try:
                    zip_ref.extract(macosx_weird_file, temp_dir)
                except:
                    pass

            # If there was associated metadata, tries to incorporate them
            if os.path.exists(temp_dir + '/__MACOSX/'):
                extracted_archive_path = os.path.join(temp_dir, zip_name)
                shell_command = 'rsync -a ' + extracted_archive_path + '/ ' + temp_dir + '/__MACOSX/'
                subprocess.run(shell_command, cwd=temp_dir, shell=True, check=True)
                shell_command = 'dot_clean -v --keep=dotbar ' + extracted_archive_path + ' __MACOSX/'
                subprocess.run(shell_command, cwd=temp_dir, shell=True, check=True)
                extraction_folder = temp_dir + '/__MACOSX/'
            else:
                extraction_folder = os.path.join(temp_dir, zip_name)

            extraction_path = os.path.join(extraction_folder, to_extract)

            # Determine the destination folder
            destination_folder = os.getenv('destination_folder')
            if destination_folder == "":
                destination_folder = zip_directory
            else:
                destination_folder = os.path.expanduser(destination_folder)
                if not os.path.isdir(destination_folder):
                    comment = f'Folder {destination_folder} is not recognized as a folder.' 
                    alfred_error_message(comment, next_directory, zip_file)
                    return
            
            # Change the final name of the extraction if a file with the same name already exists
            # in the destination folder
            base_extraction_name = os.path.basename(os.path.normpath(to_extract))
            new_extraction_name = base_extraction_name

            new_extraction_path = os.path.join(destination_folder, new_extraction_name)
            i = 0
            if os.path.isfile(new_extraction_path):
                name, ext = os.path.splitext(new_extraction_name)
                while os.path.exists(new_extraction_path):
                    i += 1
                    new_extraction_name = f"{name}-{i}{ext}"
                    new_extraction_path = os.path.join(destination_folder, new_extraction_name)
            else:
                name = new_extraction_name
                while os.path.exists(new_extraction_path):
                    i += 1
                    new_extraction_name = f"{name}-{i}"
                    new_extraction_path = os.path.join(destination_folder, new_extraction_name)
            
            if i>0:
                shutil.move(extraction_path, os.path.join(extraction_folder, new_extraction_name))
                extraction_path = os.path.join(extraction_folder, new_extraction_name)
            
            # Move the extracted file/folder to the user's destination and prepare the notification
            try:
                shutil.move(extraction_path, destination_folder)
                
                if i ==0:
                    comment = f"'{base_extraction_name}' was successfully extracted from '{zip_name}.zip'." 
                else:
                    comment = f"'{base_extraction_name}' existed in destination folder and was " \
                        f"extracted from '{zip_name}.zip' as '{new_extraction_name}'."
                notify_and_reveal(comment, next_directory, new_extraction_name, destination_folder, zip_file)

            except Exception as e:
                comment = "Error: " + str(e)
                alfred_error_message(comment, next_directory, zip_file)
                return
            
def main():
    zip_file = os.getenv('zip_file')
    to_extract = os.getenv('file_to_extract')
    next_directory = os.getenv('next_directory')
    extract_folder_from_zip(zip_file, to_extract, next_directory)

if __name__ == "__main__":
    main()

